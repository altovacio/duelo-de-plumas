from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List

from app.db.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserCredit, UserResponse
from app.db.models.user import User

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
        
    async def get_user(self, user_id: int):
        """Get a user by ID."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
        
    async def get_users(self, skip: int = 0, limit: int = 100):
        """Get all users with pagination."""
        return await self.repository.get_all(skip, limit)
        
    async def get_users_with_contest_counts(self, skip: int = 0, limit: int = 100):
        """Get all users with their contest counts using an optimized query."""
        return await self.repository.get_all_with_contest_counts(skip, limit)
        
    async def search_users(self, query: str, limit: int = 10):
        """Search users by username or email."""
        return await self.repository.search_users(query, limit)
        
    async def get_users_by_ids(self, user_ids: List[int]):
        """Get multiple users by their IDs."""
        return await self.repository.get_users_by_ids(user_ids)
        
    async def create_user(self, user_data: UserCreate):
        """Create a new user."""
        # Check if username exists
        user = await self.repository.get_by_username(user_data.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
            
        # Check if email exists
        user = await self.repository.get_by_email(user_data.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        return await self.repository.create(user_data)
        
    async def update_user(self, user_id: int, user_data: UserUpdate, current_user: User):
        """Update a user."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Check permissions (only the user themselves or an admin can update a user)
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        # If updating email, check if new email already exists
        if user_data.email is not None and user_data.email != user.email:
            existing_user = await self.repository.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
                
        return await self.repository.update(user_id, user_data)
        
    async def delete_user(self, user_id: int, current_user: User):
        """Delete a user."""
        # Only admins can delete users
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Delete the user
        await self.repository.delete(user_id)
        
        # Additional cleanup will be needed here (e.g., cascade delete related entities)
        # This should be handled in a transaction
        
        return True
        
    async def update_user_credits(self, user_id: int, credit_data: UserCredit, current_user: User):
        """Update a user's credits."""
        # Only admins can update user credits
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return await self.repository.update_credits(user_id, credit_data) 