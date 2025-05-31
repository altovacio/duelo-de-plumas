from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.contest_member import ContestMember
from app.db.models.text import Text
from app.schemas.contest import ContestCreate, ContestUpdate


class ContestRepository:
    @staticmethod
    async def create_contest(db: AsyncSession, contest: ContestCreate, creator_id: int) -> Contest:
        db_contest = Contest(
            title=contest.title,
            description=contest.description,
            password_protected=contest.password_protected,
            password=contest.password,
            publicly_listed=contest.publicly_listed,
            min_votes_required=contest.min_votes_required,
            end_date=contest.end_date,
            judge_restrictions=contest.judge_restrictions,
            author_restrictions=contest.author_restrictions,
            creator_id=creator_id
        )
        db.add(db_contest)
        await db.commit()
        await db.refresh(db_contest)
        
        # If the contest is not publicly listed, automatically add the creator as a member
        if not contest.publicly_listed:
            await ContestRepository.add_member_to_contest(db, db_contest.id, creator_id)
        
        return db_contest
    
    @staticmethod
    async def get_contests_with_counts(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        current_user_id: Optional[int] = None,
        creator_id: Optional[Union[int, str]] = None,
        include_non_public: bool = False
    ) -> List[dict]:
        """Get contests with counts in a single optimized query to avoid N+1 problem."""
        
        # Subquery for text count per contest
        text_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(ContestText.text_id)).label("text_count")
            )
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Subquery for participant count per contest
        participant_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(Text.owner_id)).label("participant_count")
            )
            .join(Text, ContestText.text_id == Text.id)
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Main query with left joins to get counts
        query = (
            select(
                Contest,
                func.coalesce(text_count_subq.c.text_count, 0).label("text_count"),
                func.coalesce(participant_count_subq.c.participant_count, 0).label("participant_count")
            )
            .outerjoin(text_count_subq, Contest.id == text_count_subq.c.contest_id)
            .outerjoin(participant_count_subq, Contest.id == participant_count_subq.c.contest_id)
            .options(selectinload(Contest.creator))
        )
        
        # Apply filters
        if status:
            query = query.where(Contest.status.ilike(f"%{status}%"))
            
        if creator_id is not None:
            # Handle string values for creator_id by casting to int
            if isinstance(creator_id, str) and creator_id.isdigit():
                creator_id = int(creator_id)
            query = query.where(Contest.creator_id == creator_id)
        
        # Filter by visibility unless explicitly including non-public contests
        if not include_non_public:
            query = query.where(Contest.publicly_listed == True)
        
        # Execute query with ordering and pagination
        result = await db.execute(
            query.order_by(Contest.created_at.desc()).offset(skip).limit(limit)
        )
        
        # Convert results to dictionaries
        contests_with_counts = []
        for row in result.all():
            contest_obj = row.Contest
            
            # Convert the Contest ORM instance to a dictionary
            contest_data = {column.key: getattr(contest_obj, column.key) for column in Contest.__table__.columns}
            
            # Add the counts
            contest_data["text_count"] = row.text_count
            contest_data["participant_count"] = row.participant_count
            
            # Add creator information
            if contest_obj.creator:
                contest_data["creator"] = {
                    "id": contest_obj.creator.id,
                    "username": contest_obj.creator.username
                }
            else:
                contest_data["creator"] = {
                    "id": contest_data["creator_id"],
                    "username": "Unknown"
                }
            
            # Remove creator_id since we now use the creator object
            contest_data.pop("creator_id", None)
            
            # Add has_password field
            contest_data["has_password"] = bool(contest_data.get("password"))
            
            contests_with_counts.append(contest_data)
        
        return contests_with_counts
    
    @staticmethod
    async def get_contests(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        current_user_id: Optional[int] = None,
        creator_id: Optional[Union[int, str]] = None,
        include_non_public: bool = False
    ) -> List[Contest]:
        """Get a list of contests with optional filtering.
        If status is provided, filter by status.
        If creator_id is provided, filter by creator_id.
        
        Note: This method returns Contest ORM objects. For contests with counts,
        use get_contests_with_counts() instead.
        """
        query = select(Contest).options(selectinload(Contest.creator))
        
        if status:
            query = query.where(Contest.status.ilike(f"%{status}%"))
            
        if creator_id is not None:
            # Handle string values for creator_id by casting to int
            if isinstance(creator_id, str) and creator_id.isdigit():
                creator_id = int(creator_id)
            query = query.where(Contest.creator_id == creator_id)
        
        # Filter by visibility unless explicitly including non-public contests
        if not include_non_public:
            query = query.where(Contest.publicly_listed == True)
            
        # The comment below is for the general case of listing all contests.
        # Specific views like "My Contests" will use the creator_id filter.
        # Only publicly listed contests are shown by default; details are protected by GET /{id}
            
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

        # Main query: Select Contest ORM, counts, and load judges and members
        stmt = select(
            Contest, # Select the Contest ORM entity
            text_count_subq.label("text_count"),
            participant_count_subq.label("participant_count")
        ).options(
            selectinload(Contest.contest_judges), # Load contest judges
            selectinload(Contest.contest_members).selectinload(ContestMember.user), # Load contest members with user info
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
        contest_data["judges"] = contest_obj.contest_judges
        
        # Add the loaded members (will be ORM objects, Pydantic handles conversion)
        contest_data["members"] = contest_obj.contest_members
        
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
    async def get_contests_for_judge(db: AsyncSession, user_judge_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all contests where the given user_id is a judge with counts."""
        
        # Subquery for text count per contest
        text_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(ContestText.text_id)).label("text_count")
            )
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Subquery for participant count per contest
        participant_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(Text.owner_id)).label("participant_count")
            )
            .join(Text, ContestText.text_id == Text.id)
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Main query with joins for counts
        stmt = (
            select(
                Contest,
                func.coalesce(text_count_subq.c.text_count, 0).label("text_count"),
                func.coalesce(participant_count_subq.c.participant_count, 0).label("participant_count")
            )
            .join(ContestJudge, Contest.id == ContestJudge.contest_id)
            .outerjoin(text_count_subq, Contest.id == text_count_subq.c.contest_id)
            .outerjoin(participant_count_subq, Contest.id == participant_count_subq.c.contest_id)
            .filter(ContestJudge.user_judge_id == user_judge_id)
            .options(selectinload(Contest.creator))  # Load creator relationship
            .order_by(Contest.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        
        # Convert ORM objects to dictionaries with creator information and counts
        contest_dicts = []
        for row in result.all():
            contest = row.Contest
            contest_data = {column.key: getattr(contest, column.key) for column in Contest.__table__.columns}
            
            # Add creator information
            if contest.creator:
                contest_data["creator"] = {
                    "id": contest.creator.id,
                    "username": contest.creator.username
                }
            else:
                contest_data["creator"] = {
                    "id": contest_data["creator_id"],
                    "username": "Unknown"
                }
            
            # Remove creator_id since we now use the creator object
            contest_data.pop("creator_id", None)
            
            # Add the actual counts from the query
            contest_data["text_count"] = row.text_count
            contest_data["participant_count"] = row.participant_count
            
            # Add has_password field
            contest_data["has_password"] = bool(contest_data.get("password"))
            
            contest_dicts.append(contest_data)
        
        return contest_dicts
    
    # Methods for contest member management
    @staticmethod
    async def add_member_to_contest(db: AsyncSession, contest_id: int, user_id: int) -> Optional[ContestMember]:
        """Add a member to a contest."""
        # Check if member already exists
        stmt = select(ContestMember).filter(
            ContestMember.contest_id == contest_id,
            ContestMember.user_id == user_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return None  # Already a member
            
        db_contest_member = ContestMember(
            contest_id=contest_id,
            user_id=user_id
        )
        db.add(db_contest_member)
        await db.commit()
        await db.refresh(db_contest_member)
        return db_contest_member
    
    @staticmethod
    async def remove_member_from_contest(db: AsyncSession, contest_id: int, user_id: int) -> bool:
        """Remove a member from a contest."""
        stmt = select(ContestMember).filter(
            ContestMember.contest_id == contest_id,
            ContestMember.user_id == user_id
        )
        result = await db.execute(stmt)
        db_contest_member = result.scalar_one_or_none()
        
        if not db_contest_member:
            return False
            
        await db.delete(db_contest_member)
        await db.commit()
        return True
    
    @staticmethod
    async def get_contest_members(db: AsyncSession, contest_id: int) -> List[ContestMember]:
        """Get all members of a contest."""
        stmt = select(ContestMember).filter(
            ContestMember.contest_id == contest_id
        ).options(
            selectinload(ContestMember.user)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def is_contest_member(db: AsyncSession, contest_id: int, user_id: int) -> bool:
        """Check if a user is a member of a contest."""
        stmt = select(ContestMember).filter(
            ContestMember.contest_id == contest_id,
            ContestMember.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def get_contests_for_author(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all contests where the given user has submitted texts as an author with counts."""
        from app.db.models.contest_text import ContestText
        from app.db.models.text import Text
        
        # Subquery for text count per contest
        text_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(ContestText.text_id)).label("text_count")
            )
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Subquery for participant count per contest
        participant_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(Text.owner_id)).label("participant_count")
            )
            .join(Text, ContestText.text_id == Text.id)
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Main query with joins for counts
        stmt = (
            select(
                Contest,
                func.coalesce(text_count_subq.c.text_count, 0).label("text_count"),
                func.coalesce(participant_count_subq.c.participant_count, 0).label("participant_count")
            )
            .join(ContestText, Contest.id == ContestText.contest_id)
            .join(Text, ContestText.text_id == Text.id)
            .outerjoin(text_count_subq, Contest.id == text_count_subq.c.contest_id)
            .outerjoin(participant_count_subq, Contest.id == participant_count_subq.c.contest_id)
            .filter(Text.owner_id == user_id)
            .options(selectinload(Contest.creator))  # Load creator relationship
            .distinct()
            .order_by(Contest.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        
        # Convert ORM objects to dictionaries with creator information and counts
        contest_dicts = []
        for row in result.all():
            contest = row.Contest
            contest_data = {column.key: getattr(contest, column.key) for column in Contest.__table__.columns}
            
            # Add creator information
            if contest.creator:
                contest_data["creator"] = {
                    "id": contest.creator.id,
                    "username": contest.creator.username
                }
            else:
                contest_data["creator"] = {
                    "id": contest_data["creator_id"],
                    "username": "Unknown"
                }
            
            # Remove creator_id since we now use the creator object
            contest_data.pop("creator_id", None)
            
            # Add the actual counts from the query
            contest_data["text_count"] = row.text_count
            contest_data["participant_count"] = row.participant_count
            
            # Add has_password field
            contest_data["has_password"] = bool(contest_data.get("password"))
            
            contest_dicts.append(contest_data)
        
        return contest_dicts
    
    @staticmethod
    async def get_contests_for_member(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all contests where the given user is a member with counts."""
        
        # Subquery for text count per contest
        text_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(ContestText.text_id)).label("text_count")
            )
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Subquery for participant count per contest
        participant_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(Text.owner_id)).label("participant_count")
            )
            .join(Text, ContestText.text_id == Text.id)
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Main query with joins for counts
        stmt = (
            select(
                Contest,
                func.coalesce(text_count_subq.c.text_count, 0).label("text_count"),
                func.coalesce(participant_count_subq.c.participant_count, 0).label("participant_count")
            )
            .join(ContestMember, Contest.id == ContestMember.contest_id)
            .outerjoin(text_count_subq, Contest.id == text_count_subq.c.contest_id)
            .outerjoin(participant_count_subq, Contest.id == participant_count_subq.c.contest_id)
            .filter(ContestMember.user_id == user_id)
            .options(selectinload(Contest.creator))  # Load creator relationship
            .order_by(Contest.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        
        # Convert ORM objects to dictionaries with creator information and counts
        contest_dicts = []
        for row in result.all():
            contest = row.Contest
            contest_data = {column.key: getattr(contest, column.key) for column in Contest.__table__.columns}
            
            # Add creator information
            if contest.creator:
                contest_data["creator"] = {
                    "id": contest.creator.id,
                    "username": contest.creator.username
                }
            else:
                contest_data["creator"] = {
                    "id": contest_data["creator_id"],
                    "username": "Unknown"
                }
            
            # Remove creator_id since we now use the creator object
            contest_data.pop("creator_id", None)
            
            # Add the actual counts from the query
            contest_data["text_count"] = row.text_count
            contest_data["participant_count"] = row.participant_count
            
            # Add has_password field
            contest_data["has_password"] = bool(contest_data.get("password"))
            
            contest_dicts.append(contest_data)
        
        return contest_dicts 
    
    @staticmethod
    async def search_contests(
        db: AsyncSession,
        search_query: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        creator_id: Optional[Union[int, str]] = None,
        include_non_public: bool = False
    ) -> List[dict]:
        """Search contests by title or description with counts."""
        search_pattern = f"%{search_query}%"
        
        # Subquery for text count per contest
        text_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(ContestText.text_id)).label("text_count")
            )
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Subquery for participant count per contest
        participant_count_subq = (
            select(
                ContestText.contest_id,
                func.count(func.distinct(Text.owner_id)).label("participant_count")
            )
            .join(Text, ContestText.text_id == Text.id)
            .group_by(ContestText.contest_id)
            .subquery()
        )
        
        # Main query with search filter
        query = (
            select(
                Contest,
                func.coalesce(text_count_subq.c.text_count, 0).label("text_count"),
                func.coalesce(participant_count_subq.c.participant_count, 0).label("participant_count")
            )
            .outerjoin(text_count_subq, Contest.id == text_count_subq.c.contest_id)
            .outerjoin(participant_count_subq, Contest.id == participant_count_subq.c.contest_id)
            .options(selectinload(Contest.creator))
            .where(
                (Contest.title.ilike(search_pattern)) | 
                (Contest.description.ilike(search_pattern))
            )
        )
        
        # Apply additional filters
        if status:
            query = query.where(Contest.status.ilike(f"%{status}%"))
            
        if creator_id is not None:
            if isinstance(creator_id, str) and creator_id.isdigit():
                creator_id = int(creator_id)
            query = query.where(Contest.creator_id == creator_id)
        
        # Filter by visibility unless explicitly including non-public contests
        if not include_non_public:
            query = query.where(Contest.publicly_listed == True)
        
        # Execute query with ordering and pagination
        result = await db.execute(
            query.order_by(Contest.created_at.desc()).offset(skip).limit(limit)
        )
        
        # Convert results to dictionaries
        contests_with_counts = []
        for row in result.all():
            contest_obj = row.Contest
            
            # Convert the Contest ORM instance to a dictionary
            contest_data = {column.key: getattr(contest_obj, column.key) for column in Contest.__table__.columns}
            
            # Add the counts
            contest_data["text_count"] = row.text_count
            contest_data["participant_count"] = row.participant_count
            
            # Add creator information
            if contest_obj.creator:
                contest_data["creator"] = {
                    "id": contest_obj.creator.id,
                    "username": contest_obj.creator.username
                }
            else:
                contest_data["creator"] = {
                    "id": contest_data["creator_id"],
                    "username": "Unknown"
                }
            
            # Remove creator_id since we now use the creator object
            contest_data.pop("creator_id", None)
            
            # Add has_password field
            contest_data["has_password"] = bool(contest_data.get("password"))
            
            contests_with_counts.append(contest_data)
        
        return contests_with_counts 