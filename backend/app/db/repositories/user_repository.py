from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserCredit
from app.core.security import get_password_hash

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_by_id(self, user_id: int) -> User:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
        
    async def get_by_username(self, username: str) -> User:
        """Get a user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()
        
    async def get_by_email(self, email: str) -> User:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()
        
    async def get_all(self, skip: int = 0, limit: int = 100):
        """Get all users with pagination."""
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
        
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_admin=False,  # Default to regular user
            credits=0  # Start with 0 credits
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
        
    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Update a user."""
        update_data = user_data.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.fetchone()
        
    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        stmt = delete(User).where(User.id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return True
        
    async def update_credits(self, user_id: int, credit_data: UserCredit) -> User:
        """Update a user's credits."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(credits=credit_data.credits)
            .returning(User)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.fetchone() 