from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column, case
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.schemas.contest import ContestCreate, ContestUpdate


class ContestRepository:
    @staticmethod
    async def create_contest(db: AsyncSession, contest: ContestCreate, creator_id: int) -> Contest:
        db_contest = Contest(
            title=contest.title,
            description=contest.description,
            is_private=contest.is_private,
            password=contest.password,
            min_votes_required=contest.min_votes_required,
            end_date=contest.end_date,
            judge_restrictions=contest.judge_restrictions,
            author_restrictions=contest.author_restrictions,
            creator_id=creator_id
        )
        db.add(db_contest)
        await db.commit()
        await db.refresh(db_contest)
        return db_contest
    
    @staticmethod
    async def get_contests(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        is_private: Optional[bool] = None,
        creator_id: Optional[int] = None
    ) -> List[Contest]:
        query = select(Contest)
        
        # Apply filters if provided
        if state:
            query = query.where(Contest.state == state)
        if is_private is not None:
            query = query.where(Contest.is_private == is_private)
        if creator_id:
            query = query.where(Contest.creator_id == creator_id)
            
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def get_contest(db: AsyncSession, contest_id: int) -> Optional[Contest]:
        result = await db.execute(select(Contest).filter(Contest.id == contest_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_contest(
        db: AsyncSession, contest_id: int, contest_update: ContestUpdate
    ) -> Optional[Contest]:
        stmt = select(Contest).filter(Contest.id == contest_id)
        result = await db.execute(stmt)
        db_contest = result.scalar_one_or_none()

        if not db_contest:
            return None
        
        update_data = contest_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_contest, key, value)
        
        await db.commit()
        await db.refresh(db_contest)
        return db_contest
    
    @staticmethod
    async def delete_contest(db: AsyncSession, contest_id: int) -> bool:
        stmt = select(Contest).filter(Contest.id == contest_id)
        result = await db.execute(stmt)
        db_contest = result.scalar_one_or_none()

        if not db_contest:
            return False
        
        await db.delete(db_contest)
        await db.commit()
        return True
    
    @staticmethod
    async def get_contest_with_counts(db: AsyncSession, contest_id: int) -> Optional[dict]:
        """Get contest with participant count and text count"""
        stmt = select(
            Contest,
            func.count(func.distinct(ContestText.text_id)).label("text_count"),
            func.count(func.distinct(ContestJudge.judge_id)).label("participant_count")
        ).outerjoin(
            ContestText, ContestText.contest_id == Contest.id
        ).outerjoin(
            ContestJudge, ContestJudge.contest_id == Contest.id
        ).filter(
            Contest.id == contest_id
        ).group_by(
            Contest.id
        )
        result = await db.execute(stmt)
        record = result.first()

        if not record:
            return None
            
        return {
            "contest": record[0],
            "text_count": record.text_count,
            "participant_count": record.participant_count
        }
    
    # Methods for contest text submissions
    @staticmethod
    async def submit_text_to_contest(db: AsyncSession, contest_id: int, text_id: int) -> Optional[ContestText]:
        stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == text_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return None  # Already submitted
            
        db_contest_text = ContestText(
            contest_id=contest_id,
            text_id=text_id
        )
        db.add(db_contest_text)
        await db.commit()
        await db.refresh(db_contest_text)
        return db_contest_text
    
    @staticmethod
    async def get_contest_texts(db: AsyncSession, contest_id: int) -> List[ContestText]:
        stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def remove_text_from_contest(db: AsyncSession, contest_id: int, text_id: int) -> bool:
        stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == text_id
        )
        result = await db.execute(stmt)
        db_contest_text = result.scalar_one_or_none()
        
        if not db_contest_text:
            return False
            
        await db.delete(db_contest_text)
        await db.commit()
        return True
    
    # Methods for contest judge assignments
    @staticmethod
    async def assign_judge_to_contest(db: AsyncSession, contest_id: int, judge_id: int) -> Optional[ContestJudge]:
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return None  # Already assigned
            
        db_contest_judge = ContestJudge(
            contest_id=contest_id,
            judge_id=judge_id
        )
        db.add(db_contest_judge)
        await db.commit()
        await db.refresh(db_contest_judge)
        return db_contest_judge
    
    @staticmethod
    async def get_contest_judges(db: AsyncSession, contest_id: int) -> List[ContestJudge]:
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def remove_judge_from_contest(db: AsyncSession, contest_id: int, judge_id: int) -> bool:
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        )
        result = await db.execute(stmt)
        db_contest_judge = result.scalar_one_or_none()
        
        if not db_contest_judge:
            return False
            
        await db.delete(db_contest_judge)
        await db.commit()
        return True
    
    @staticmethod
    async def get_contests_for_judge(db: AsyncSession, judge_id: int, skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get all contests where the given user_id is a judge."""
        stmt = select(Contest).join(ContestJudge, Contest.id == ContestJudge.contest_id).filter(
            ContestJudge.judge_id == judge_id
        ).order_by(Contest.id.desc()).offset(skip).limit(limit) # Added order_by and pagination
        
        result = await db.execute(stmt)
        return result.scalars().all() 