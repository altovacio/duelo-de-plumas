from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Text, User
from app.db.models.contest_text import ContestText
from app.db.models.contest import Contest
from app.schemas.text import TextCreate, TextUpdate


class TextRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_text(self, text_data: TextCreate, owner_id: int) -> Text:
        db_text = Text(
            title=text_data.title,
            content=text_data.content,
            author=text_data.author,
            owner_id=owner_id
        )
        self.db.add(db_text)
        await self.db.commit()
        await self.db.refresh(db_text)
        return db_text
    
    async def get_text(self, text_id: int) -> Optional[Text]:
        stmt = select(Text).filter(Text.id == text_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_texts(self, skip: int = 0, limit: int = 100) -> List[Text]:
        stmt = select(Text).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_texts(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Text]:
        stmt = select(Text).filter(Text.owner_id == owner_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_text(self, text_id: int, text_data: TextUpdate) -> Optional[Text]:
        db_text = await self.get_text(text_id)
        if db_text is None:
            return None
        
        update_data = text_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_text, key, value)
        
        await self.db.commit()
        await self.db.refresh(db_text)
        return db_text
    
    async def delete_text(self, text_id: int) -> bool:
        db_text = await self.get_text(text_id)
        if db_text is None:
            return False
        
        await self.db.delete(db_text)
        await self.db.commit()
        return True
    
    async def get_contest_text(self, text_id: int) -> Optional[ContestText]:
        # Get the most recent contest text entry for this text
        stmt = select(ContestText).filter(
            ContestText.text_id == text_id
        ).order_by(ContestText.submission_date.desc())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_contest(self, contest_id: int) -> Optional[Contest]:
        stmt = select(Contest).filter(Contest.id == contest_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_contest_texts(self, text_id: int) -> List[ContestText]:
        stmt = select(ContestText).filter(ContestText.text_id == text_id)
        result = await self.db.execute(stmt)
        return result.scalars().all() 