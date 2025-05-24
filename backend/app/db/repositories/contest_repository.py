from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.text import Text
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
        status: Optional[str] = None,
        current_user_id: Optional[int] = None,
        creator_id: Optional[Union[int, str]] = None
    ) -> List[Contest]:
        """Get a list of contests with optional filtering.
        If status is provided, filter by status.
        If creator_id is provided, filter by creator_id.
        """
        query = select(Contest).options(selectinload(Contest.creator))
        
        if status:
            query = query.where(Contest.status.ilike(f"%{status}%"))
            
        if creator_id is not None:
            # Handle string values for creator_id by casting to int
            if isinstance(creator_id, str) and creator_id.isdigit():
                creator_id = int(creator_id)
            query = query.where(Contest.creator_id == creator_id)
            
        # The comment below is for the general case of listing all contests.
        # Specific views like "My Contests" will use the creator_id filter.
        # All contests are listed; details are protected by GET /{id}
            
        result = await db.execute(query.order_by(Contest.created_at.desc()).offset(skip).limit(limit))
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
        """Get contest with participant count, text count, and judges."""
        # Subquery for text count
        text_count_subq = select(
            func.count(func.distinct(ContestText.text_id)).label("text_count")
        ).where(
            ContestText.contest_id == contest_id
        ).scalar_subquery()
        
        # Subquery for participant count
        participant_count_subq = select(
            func.count(func.distinct(Text.owner_id)).label("participant_count")
        ).join(
            ContestText, ContestText.text_id == Text.id
        ).where(
            ContestText.contest_id == contest_id
        ).scalar_subquery()

        # Main query: Select Contest ORM, counts, and load judges
        stmt = select(
            Contest, # Select the Contest ORM entity
            text_count_subq.label("text_count"),
            participant_count_subq.label("participant_count")
        ).options(
            selectinload(Contest.contest_judges), # Changed to Contest.contest_judges
            selectinload(Contest.creator) # Load creator relationship
        ).filter(Contest.id == contest_id)
        
        result = await db.execute(stmt)
        record = result.first()

        if not record:
            return None
            
        contest_obj = record.Contest # Access the Contest ORM instance with judges loaded
        
        # Convert the Contest ORM instance to a dictionary
        contest_data = {column.key: getattr(contest_obj, column.key) for column in Contest.__table__.columns}
        
        # Add the counts
        contest_data["text_count"] = record.text_count
        contest_data["participant_count"] = record.participant_count
        
        # Add creator information - this is now required
        if contest_obj.creator:
            contest_data["creator"] = {
                "id": contest_obj.creator.id,
                "username": contest_obj.creator.username
            }
        else:
            # Fallback if creator relationship is not loaded properly
            contest_data["creator"] = {
                "id": contest_data["creator_id"],
                "username": "Unknown"
            }
        
        # Remove creator_id since we now use the creator object
        contest_data.pop("creator_id", None)
        
        # Add the loaded judges (will be ORM objects, Pydantic handles conversion)
        contest_data["judges"] = contest_obj.contest_judges # Changed to contest_obj.contest_judges
        
        return contest_data
    
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
        ).options(
            selectinload(ContestText.text)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_submission_by_id(db: AsyncSession, submission_id: int) -> Optional[ContestText]:
        """Gets a specific ContestText entry by its primary key."""
        stmt = select(ContestText).filter(ContestText.id == submission_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def remove_text_from_contest(db: AsyncSession, contest_id: int, text_id: int) -> bool:
        # This method deletes by (contest_id, text_id) pair.
        # It might still be used if there's a use case to remove a specific text from a contest
        # regardless of how many times it was submitted (if multiple submissions of same text were allowed and distinct).
        # However, current E2E tests pass submission_id (ContestText.id) to this, which is wrong for its current logic.
        # For now, let's assume the primary way to delete a submission is by its unique submission_id (ContestText.id)
        stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == text_id  # This identifies ONE submission of a text to a contest.
                                          # If a text could be submitted multiple times creating multiple ContestText entries
                                          # for the same (text_id, contest_id), this would only delete one.
                                          # However, submit_text_to_contest checks for existing and returns None if already submitted.
                                          # So, there's typically only one ContestText per (text_id, contest_id).
        )
        result = await db.execute(stmt)
        db_contest_text = result.scalar_one_or_none()
        
        if not db_contest_text:
            return False
            
        await db.delete(db_contest_text)
        await db.commit()
        return True
    
    @staticmethod
    async def delete_submission(db: AsyncSession, submission_id: int) -> bool:
        """Deletes a specific ContestText entry by its primary key (submission_id)."""
        db_submission = await ContestRepository.get_submission_by_id(db, submission_id)
        
        if not db_submission:
            return False
            
        await db.delete(db_submission)
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
    async def get_contest_judge_by_id(db: AsyncSession, contest_judge_id: int) -> Optional[ContestJudge]:
        """Gets a specific ContestJudge entry by its primary key."""
        stmt = select(ContestJudge).filter(ContestJudge.id == contest_judge_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_contest_judges(db: AsyncSession, contest_id: int) -> List[ContestJudge]:
        stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def remove_judge_from_contest(db: AsyncSession, contest_id: int, contest_judge_id: int) -> bool:
        """Remove a specific judge assignment entry by its ID."""
        stmt = select(ContestJudge).filter(
            ContestJudge.id == contest_judge_id, # Filter by the specific assignment ID
            ContestJudge.contest_id == contest_id # Ensure it belongs to the correct contest
        )
        result = await db.execute(stmt)
        db_contest_judge = result.scalar_one_or_none()
        
        if not db_contest_judge:
            return False # Assignment not found or doesn't belong to this contest
            
        await db.delete(db_contest_judge)
        await db.commit()
        return True
    
    @staticmethod
    async def get_contests_for_judge(db: AsyncSession, user_judge_id: int, skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get all contests where the given user_id is a judge."""
        stmt = select(Contest).join(ContestJudge, Contest.id == ContestJudge.contest_id).filter(
            ContestJudge.user_judge_id == user_judge_id # Filter by user judge ID
        ).order_by(Contest.id.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all() 