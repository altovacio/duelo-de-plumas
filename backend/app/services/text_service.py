from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.text_repository import TextRepository
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.db.models import Text


class TextService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TextRepository(db)

    async def create_text(self, text_data: TextCreate, current_user_id: int) -> Text:
        # Create the text with the current user as owner
        db_text = await self.repository.create_text(text_data, current_user_id)
        return db_text
    
    async def get_text(self, text_id: int, current_user_id: Optional[int] = None) -> Text:
        # Get a text by ID
        db_text = await self.repository.get_text(text_id)
        if db_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )
            
        # Check if text is part of any contest in evaluation or closed phase
        contest_texts = await self.repository.get_contest_texts(text_id)
        for contest_text in contest_texts:
            contest = await self.repository.get_contest(contest_text.contest_id)
            if contest and contest.status.lower() in ["evaluation", "closed"]:
                # If text is in any contest in evaluation or closed phase, allow access
                return db_text
                
        # For texts not in any evaluation/closed contest, require authentication
        if current_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        return db_text
    
    async def get_texts(self, skip: int = 0, limit: int = 100) -> List[Text]:
        # Get all texts
        return await self.repository.get_texts(skip, limit)
    
    async def get_user_texts(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Text]:
        # Get texts belonging to a specific user
        return await self.repository.get_user_texts(user_id, skip, limit)
    
    async def update_text(self, text_id: int, text_data: TextUpdate, current_user_id: int, is_admin: bool = False) -> Text:
        # Check if text exists
        db_text = await self.repository.get_text(text_id)
        if db_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )
        
        # Check if user is owner or admin
        if db_text.owner_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this text"
            )
        
        # Update the text
        updated_text = await self.repository.update_text(text_id, text_data)
        return updated_text
    
    async def delete_text(self, text_id: int, current_user_id: int, is_admin: bool = False) -> bool:
        # Check if text exists
        db_text = await self.repository.get_text(text_id)
        if db_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )
        
        # Check if user is owner or admin
        if db_text.owner_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this text"
            )
        
        # Delete the text
        result = await self.repository.delete_text(text_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error deleting text or text not found"
            )
        return True 