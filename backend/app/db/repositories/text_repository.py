from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Text, User
from app.schemas.text import TextCreate, TextUpdate


class TextRepository:
    def create_text(self, db: Session, text_data: TextCreate, owner_id: int) -> Text:
        db_text = Text(
            title=text_data.title,
            content=text_data.content,
            author=text_data.author,
            owner_id=owner_id
        )
        db.add(db_text)
        db.commit()
        db.refresh(db_text)
        return db_text
    
    def get_text(self, db: Session, text_id: int) -> Optional[Text]:
        return db.query(Text).filter(Text.id == text_id).first()
    
    def get_texts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Text]:
        return db.query(Text).offset(skip).limit(limit).all()
    
    def get_user_texts(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Text]:
        return db.query(Text).filter(Text.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def update_text(self, db: Session, text_id: int, text_data: TextUpdate) -> Optional[Text]:
        db_text = self.get_text(db, text_id)
        if db_text is None:
            return None
        
        update_data = text_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_text, key, value)
        
        db.commit()
        db.refresh(db_text)
        return db_text
    
    def delete_text(self, db: Session, text_id: int) -> bool:
        db_text = self.get_text(db, text_id)
        if db_text is None:
            return False
        
        db.delete(db_text)
        db.commit()
        return True 