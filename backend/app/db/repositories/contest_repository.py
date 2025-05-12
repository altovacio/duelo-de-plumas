from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column, case
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

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
        current_user_id: Optional[int] = None
    ) -> List[Contest]:
        query = select(Contest)
        
        # Only filter by state if provided
        if state:
            query = query.where(Contest.state == state)
            
        # Remove filtering based on is_private or creator_id for the list view
        # All contests are listed; details are protected by GET /{id}
            
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
            func.count(func.distinct(ContestJudge.id)).label("participant_count")
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
    async def assign_judge_to_contest(
        db: AsyncSession, 
        contest_id: int, 
        user_judge_id: Optional[int] = None, 
        agent_judge_id: Optional[int] = None
    ) -> Optional[ContestJudge]:
        if not (user_judge_id is not None or agent_judge_id is not None):
            # Should be caught by service/schema validation, but as a safeguard
            return None # Or raise an error

        # Check for existing assignment
        stmt = select(ContestJudge).filter(ContestJudge.contest_id == contest_id)
        if user_judge_id is not None:
            stmt = stmt.filter(ContestJudge.user_judge_id == user_judge_id)
        elif agent_judge_id is not None:
            stmt = stmt.filter(ContestJudge.agent_judge_id == agent_judge_id)
        
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Service layer will handle the HTTPException for already assigned
            return None
            
        db_contest_judge = ContestJudge(contest_id=contest_id)
        if user_judge_id is not None:
            db_contest_judge.user_judge_id = user_judge_id
        elif agent_judge_id is not None:
            db_contest_judge.agent_judge_id = agent_judge_id
        else:
            # Should not happen due to initial check
            return None

        db.add(db_contest_judge)
        try:
            await db.commit()
            await db.refresh(db_contest_judge)
            return db_contest_judge
        except IntegrityError: # Catch potential unique constraint violations not caught by prior check
            await db.rollback()
            return None # Indicate failure due to, likely, a race condition on unique constraint

    @staticmethod
    async def get_contest_judges(db: AsyncSession, contest_id: int) -> List[ContestJudge]:
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def remove_judge_from_contest(db: AsyncSession, contest_id: int, judge_id: int, judge_type: str = 'user') -> bool:
        # This method needs significant update to handle user_id or agent_id removal
        # For now, it will break if called for agents.
        # TODO: Refactor remove_judge_from_contest
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.user_judge_id == judge_id # Assumes judge_id is user_id
        )
        result = await db.execute(stmt)
        db_contest_judge = result.scalar_one_or_none()
        
        if not db_contest_judge:
            return False
            
        await db.delete(db_contest_judge)
        await db.commit()
        return True
    
    @staticmethod
    async def get_contests_for_judge(db: AsyncSession, judge_id: int, judge_type: str = 'user', skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get all contests where the given user_id or agent_id is a judge."""
        # This method needs update to handle judge_type
        # TODO: Refactor get_contests_for_judge
        stmt = select(Contest).join(ContestJudge, Contest.id == ContestJudge.contest_id).filter(
            ContestJudge.user_judge_id == judge_id # Assumes judge_id is user_id
        ).order_by(Contest.id.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all() 