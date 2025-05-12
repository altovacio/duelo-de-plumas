from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # No longer needed here if using UserRepository
from fastapi import HTTPException, status

from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash
from app.db.repositories.user_repository import UserRepository # Import UserRepository

# These functions can be removed if all calls are routed through UserRepository
# async def get_user_by_username(db: AsyncSession, username: str):
#     """Get a user by username."""
#     # result = await db.execute(select(User).where(User.username == username))
#     # return result.scalars().first()
#     user_repo = UserRepository(db)
#     return await user_repo.get_by_username(username)

# async def get_user_by_email(db: AsyncSession, email: str):
#     """Get a user by email."""
#     # result = await db.execute(select(User).where(User.email == email))
#     # return result.scalars().first()
#     user_repo = UserRepository(db)
#     return await user_repo.get_by_email(email)

async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | bool:
    """Authenticate a user."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(username)

    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user. This is typically called during registration."""
    user_repo = UserRepository(db)
    # Check if username exists
    db_user = await user_repo.get_by_username(user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email exists
    db_user = await user_repo.get_by_email(user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user using the repository's create method
    # The repository method handles hashing and db operations.
    return await user_repo.create(user_data) 