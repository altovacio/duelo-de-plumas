from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt # Import bcrypt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import settings, schemas, models, and db session from within v2
from .fastapi_config import settings
from . import schemas, models
from .database import get_db_session

# OAuth2 Scheme Setup
# Add auto_error=False to make the scheme itself optional
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# --- Password Utilities --- 

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored bcrypt hash."""
    # Ensure hashed_password is bytes, as bcrypt expects
    hashed_password_bytes = hashed_password.encode('utf-8') # Assuming stored hash is UTF-8 string
    plain_password_bytes = plain_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password=plain_password_bytes, hashed_password=hashed_password_bytes)
    except ValueError: # Handle potential errors if hash format is invalid
        return False

def get_password_hash(password: str) -> str:
    """Hashes a plain password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password=password_bytes, salt=salt)
    # Decode back to string (e.g., UTF-8) for storage in DB
    return hashed_password_bytes.decode('utf-8')

# --- JWT Token Utilities --- 

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token.
    
    Args:
        subject: The subject of the token (e.g., user ID or username).
        expires_delta: Optional timedelta for token expiry.
                      Defaults to AUTH_ACCESS_TOKEN_EXPIRE_MINUTES from settings.
    
    Returns:
        The encoded JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)} # Subject must be a string
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.AUTH_ALGORITHM
    )
    return encoded_jwt

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    """Helper function to fetch a user by username from the database."""
    result = await db.execute(select(models.User).where(models.User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Helper function to fetch a user by ID from the database."""
    # Use db.get for primary key lookup if possible and efficient with async
    user = await db.get(models.User, user_id) 
    return user

# --- Security Dependencies --- 

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme, use_cache=False), # Now explicitly Optional
    db: AsyncSession = Depends(get_db_session)
) -> models.User: # Changed return type back to User (will raise exception on failure)
    """Dependency to get the current user from the JWT token.

    Verifies token signature and expiry, fetches user from DB.
    Raises HTTPException if the token is invalid, missing, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials", # Consistent error message
        headers={"WWW-Authenticate": "Bearer"},
    )

    # DEBUG: Check if token is received
    token_preview = token[:10] + "..." if token else "None"
    print(f"Attempting to get current user from token: {token_preview}") # DEBUG
    
    if token is None:
        print("No token provided.") # DEBUG
        raise credentials_exception # Raise the consistent exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            print("  Error: Username (sub) not found in token.") # DEBUG
            raise credentials_exception # Raise exception
        token_data = schemas.TokenData(username=username)
    except (JWTError, ValidationError) as e:
        print(f"  Error decoding token: {e}") # DEBUG
        raise credentials_exception # Raise exception

    # Fetch user from database using username from token
    stmt = select(models.User).where(models.User.username == token_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        print(f"  Error: User '{token_data.username}' not found in database.") # DEBUG
        raise credentials_exception # Raise exception
        
    print(f"  Successfully authenticated user: {user.username} (ID: {user.id})") # DEBUG
    return user

# New dependency for truly optional user retrieval
async def get_optional_current_user(
    # Use Depends with the now optional scheme
    token: Optional[str] = Depends(oauth2_scheme, use_cache=False),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[models.User]:
    """Dependency to optionally get the current user.
    
    Returns the User object if token is valid, otherwise returns None.
    Relies on oauth2_scheme(auto_error=False) and get_current_user returning None.
    """
    if not token:
        return None
    # Reuse the logic from get_current_user which already handles internal errors by returning None
    return await get_current_user(token=token, db=db) 
    # Removed the redundant try/except HTTPException block

# get_current_active_user dependency needs adjustment
# It should handle the case where get_current_user returns None
# or raise 401 if the endpoint *requires* an active user.
async def get_current_active_user(
    # current_user: models.User = Depends(get_current_user) # Old dependency
    current_user: Optional[models.User] = Depends(get_current_user)
) -> models.User: # Keep return type as User, raise if None
    """Dependency that ensures a valid user is authenticated.
    
    Raises 401 if get_current_user returns None.
    Placeholder for potential future active checks.
    """
    if current_user is None:
        # This dependency requires a valid user, so raise 401 if None was returned
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated", # Or "Could not validate credentials"
            headers={"WWW-Authenticate": "Bearer"},
        )
    # if not current_user.is_active: # Example check
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Example of a dependency requiring admin role
# This now relies on get_current_active_user which handles the None case
async def require_admin(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
     """Dependency that ensures the current user is an admin."""
     if not current_user.is_admin():
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN, 
             detail="Admin privileges required"
         )
     return current_user 