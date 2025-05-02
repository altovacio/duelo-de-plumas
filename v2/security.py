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
# tokenUrl should point to the endpoint that issues tokens (we'll create this soon)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

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
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> models.User:
    """Dependency to get the current user from the JWT token.
    
    Verifies token signature and expiry, fetches user from DB.
    Raises HTTPException if token is invalid or user not found.
    """
    print(f"Attempting to get current user from token: {token[:10]}...") # DEBUG
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM]
        )
        username: str = payload.get("sub")
        print(f"  Token payload decoded. Username (sub): {username}") # DEBUG
        if username is None:
            print("  Error: Username (sub) not found in token.") # DEBUG
            raise credentials_exception
        # Optionally, you could store user_id in the token instead:
        # user_id: int = int(payload.get("sub")) 
        # if user_id is None: raise credentials_exception
        # token_data = schemas.TokenData(user_id=user_id)
        token_data = schemas.TokenData(username=username)
    except (JWTError, ValidationError) as e:
        print(f"  Error decoding token: {e}") # DEBUG
        raise credentials_exception

    # Fetch user from DB based on token subject (username or user_id)
    # user = await get_user_by_id(db, token_data.user_id) 
    print(f"  Fetching user from DB with username: {token_data.username}") # DEBUG
    user = await get_user_by_username(db, token_data.username)
    
    if user is None:
        print(f"  Error: User '{token_data.username}' not found in database.") # DEBUG
        raise credentials_exception
        
    print(f"  User found: {user.username} (ID: {user.id})") # DEBUG
    return user

# Example of a dependency for requiring an active user (could add checks)
async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Dependency to get the current *active* user.
    
    Placeholder for potential future checks (e.g., user.is_active flag).
    """
    # if not current_user.is_active: # Example check
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Example of a dependency requiring admin role
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