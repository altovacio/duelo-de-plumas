from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash

async def get_user_by_username(db: AsyncSession, username: str):
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    """Get a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Authenticate a user."""
    user = await get_user_by_username(db, username)
    
    if not user:
        return False
        
    if not verify_password(password, user.hashed_password):
        return False
        
    return user

async def create_user(db: AsyncSession, user_data: UserCreate):
    """Create a new user."""
    # Check if username exists
    db_user = await get_user_by_username(db, user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email exists
    db_user = await get_user_by_email(db, user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=False,  # Default to regular user
        credits=0  # Start with 0 credits
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user 