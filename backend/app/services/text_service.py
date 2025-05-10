from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories import text_repository
from app.schemas.text import TextCreate, TextResponse, TextUpdate


class TextService:
    def create_text(self, db: Session, text_data: TextCreate, current_user_id: int) -> TextResponse:
        # Create the text with the current user as owner
        db_text = text_repository.create_text(db, text_data, current_user_id)
        return db_text
    
    def get_text(self, db: Session, text_id: int, current_user_id: Optional[int] = None) -> TextResponse:
        # Get a text by ID
        db_text = text_repository.get_text(db, text_id)
        if db_text is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found"
            )
        return db_text
    
    def get_texts(self, db: Session, skip: int = 0, limit: int = 100) -> List[TextResponse]:
        # Get all texts
        return text_repository.get_texts(db, skip, limit)
    
    def get_user_texts(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[TextResponse]:
        # Get texts belonging to a specific user
        return text_repository.get_user_texts(db, user_id, skip, limit)
    
    def update_text(self, db: Session, text_id: int, text_data: TextUpdate, current_user_id: int, is_admin: bool = False) -> TextResponse:
        # Check if text exists
        db_text = text_repository.get_text(db, text_id)
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
        updated_text = text_repository.update_text(db, text_id, text_data)
        return updated_text
    
    def delete_text(self, db: Session, text_id: int, current_user_id: int, is_admin: bool = False) -> bool:
        # Check if text exists
        db_text = text_repository.get_text(db, text_id)
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
        result = text_repository.delete_text(db, text_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting text"
            )
        return True 