from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func
from typing import List
from datetime import datetime

from app.db.models.user import User
from app.db.models.contest import Contest
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
        
    async def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin."""
        user = await self.get_by_id(user_id)
        return user.is_admin if user else False
        
    async def get_all(self, skip: int = 0, limit: int = 100):
        """Get all users with pagination."""
        result = await self.db.execute(select(User).order_by(User.id).offset(skip).limit(limit))
        return result.scalars().all()
        
    async def get_all_with_contest_counts(self, skip: int = 0, limit: int = 100):
        """Get all users with their contest counts using a single optimized query."""
        # Use a left join to get users and count their contests
        query = (
            select(
                User.id,
                User.username,
                User.email,
                User.is_admin,
                User.credits,
                User.created_at,
                User.last_login,
                func.count(Contest.id).label('contests_created')
            )
            .outerjoin(Contest, User.id == Contest.creator_id)
            .group_by(User.id, User.username, User.email, User.is_admin, User.credits, User.created_at, User.last_login)
            .order_by(User.id)
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Convert rows to user-like objects with contest counts
        users = []
        for row in rows:
            user_dict = {
                'id': row.id,
                'username': row.username,
                'email': row.email,
                'is_admin': row.is_admin,
                'credits': row.credits,
                'created_at': row.created_at,
                'last_login': row.last_login,
                'contests_created': row.contests_created
            }
            users.append(user_dict)
        
        return users
        
    async def search_users(self, query: str, skip: int = 0, limit: int = 10):
        """Search users by username or email with pagination."""
        search_pattern = f"%{query}%"
        result = await self.db.execute(
            select(User).where(
                (User.username.ilike(search_pattern)) | 
                (User.email.ilike(search_pattern))
            ).order_by(User.id).offset(skip).limit(limit)
        )
        return result.scalars().all()
        
    async def get_users_by_ids(self, user_ids: List[int]):
        """Get multiple users by their IDs."""
        if not user_ids:
            return []
        result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
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
        # First get the current user to access their current credits
        user = await self.get_by_id(user_id)
        if not user:
            return None
            
        # Calculate new credit balance by adding the amount to the current balance
        # The amount can be positive (add credits) or negative (subtract credits)
        new_credit_balance = user.credits + credit_data.amount
        
        # Make sure credits can't go below zero
        if new_credit_balance < 0:
            new_credit_balance = 0
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(credits=new_credit_balance)
            .returning(User)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.fetchone()
        
    async def update_last_login(self, user_id: int) -> User:
        """Update a user's last login time."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
            .returning(User)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.fetchone() 