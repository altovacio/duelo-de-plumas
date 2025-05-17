from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from typing import Optional

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.services.auth_service import (
    authenticate_user,
    create_user,
    # get_user_by_username # This is no longer directly imported if auth_service doesn't expose it
)
from app.core.config import settings
from app.core.security import create_access_token
from app.db.repositories.user_repository import UserRepository # Added import

router = APIRouter(tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Function to get current user from token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
        
    user_repo = UserRepository(db) # Instantiate UserRepository
    user = await user_repo.get_by_username(token_data.username) # Call instance method
    
    if user is None:
        raise credentials_exception
        
    return user

# New dependency to get user OR None if not authenticated
async def get_optional_current_user(
    request: Request, # Depend on the Request
    db: AsyncSession = Depends(get_db)
) -> Optional[UserResponse]: # Correct DB Model type hint
    token = request.headers.get("Authorization")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None or not token.startswith("Bearer "):
        return None # No token header or wrong scheme

    try:
        token_value = token.split("Bearer ")[1]
        payload = jwt.decode(
            token_value,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("id") # Added Optional just in case

        if username is None or user_id is None:
            # Invalid payload
            return None 

        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        # Invalid token (e.g., expired, bad signature)
        return None
    except IndexError:
        # Malformed Bearer token
        return None
    
    # If token is valid, try to fetch user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(token_data.username)

    if user is None:
        # User ID from token not found in DB
        return None

    return user # Valid user found

# Dependency for admin users - now depends directly on get_current_user
async def get_current_admin_user(current_user: UserResponse = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if username or email already exists
    # This will be implemented in the auth_service
    
    user = await create_user(db, user)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate and login a user.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 