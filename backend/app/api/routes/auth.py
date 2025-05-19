from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from typing import Optional, Dict

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, TokenData, UserLogin
from app.services.auth_service import (
    authenticate_user,
    create_user,
)
from app.core.config import settings
from app.core.security import create_access_token
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import User as UserModel

router = APIRouter(tags=["authentication"])

# Single OAuth2 scheme with auto_error=False
# This means if the token is not present, `Depends(oauth2_scheme)` will pass `None`
# instead of automatically raising an error.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

async def _get_user_from_token_data(
    token: Optional[str],
    db: AsyncSession
) -> Optional[UserModel]:
    """
    Internal helper to decode JWT, extract user info, and fetch user from DB.
    Returns UserModel instance or None if token is invalid, payload is bad, or user not found.
    Does NOT raise HTTPException directly for "optional" use cases.
    """
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("id")

        if username is None or user_id is None:
            # Invalid payload structure
            return None
        
        # TokenData can be used for validation if needed, but we have username and id
        # token_data = TokenData(username=username, user_id=user_id)

    except JWTError:
        # Token is invalid (e.g., expired, bad signature)
        return None
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username=username)
    return user


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel: # Returns UserModel, raises error if not authenticated
    if not token: # Token was not provided
        raise credentials_exception
        
    user = await _get_user_from_token_data(token, db)
    
    if user is None:
        # Token was provided, but was invalid, or user not found
        raise credentials_exception
        
    return user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserModel]: # Returns Optional[UserModel]
    # _get_user_from_token_data handles missing token, invalid token, or user not found by returning None.
    return await _get_user_from_token_data(token, db)


async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_user) # Depends on the new get_current_user
) -> UserModel: # Returns UserModel
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
    
    user_db = await create_user(db, user) # create_user likely returns UserModel
    return user_db # FastAPI will convert UserModel to UserResponse based on response_model

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate and login a user.
    """
    username = form_data.username
    password = form_data.password
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )
    
    user = await authenticate_user(db, username, password) # authenticate_user returns UserModel or None
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id}, # Uses attributes from UserModel
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate and login a user using JSON payload.
    """
    user = await authenticate_user(db, user_data.username, user_data.password) # authenticate_user returns UserModel or None
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id}, # Uses attributes from UserModel
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 