from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.contest import (
    ContestCreate, ContestUpdate, ContestResponse, 
    ContestDetailResponse, TextSubmission, JudgeAssignment
)
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.repositories.user_repository import UserRepository
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge


class ContestService:
    @staticmethod
    async def create_contest(db: AsyncSession, contest: ContestCreate, creator_id: int) -> Contest:
        # Validate that private contests have a password
        if contest.is_private and not contest.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private contests must have a password"
            )
            
        return await ContestRepository.create_contest(db, contest, creator_id)
    
    @staticmethod
    async def get_contests(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        state: Optional[str] = None,
        is_private: Optional[bool] = None,
        creator_id: Optional[int] = None
    ) -> List[Contest]:
        return await ContestRepository.get_contests(
            db=db, 
            skip=skip, 
            limit=limit, 
            state=state,
            is_private=is_private,
            creator_id=creator_id
        )
    
    @staticmethod
    async def get_contest(db: AsyncSession, contest_id: int) -> Contest:
        contest = await ContestRepository.get_contest(db=db, contest_id=contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest with id {contest_id} not found"
            )
        return contest
    
    @staticmethod
    async def get_contest_detail(db: AsyncSession, contest_id: int) -> Dict[str, Any]:
        result = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest with id {contest_id} not found"
            )
        return result
    
    @staticmethod
    async def update_contest(
        db: AsyncSession, 
        contest_id: int, 
        contest_update: ContestUpdate, 
        current_user_id: int
    ) -> Contest:
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Check if user is the contest creator or an admin
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        if contest.creator_id != current_user_id and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this contest"
            )
        
        # Validate state transition
        if contest_update.state and contest_update.state != contest.state:
            ContestService._validate_state_transition(contest.state, contest_update.state)
            
        # Validate that private contests have a password
        if contest_update.is_private and contest_update.is_private is True and not (
            contest_update.password or (contest.is_private and contest.password)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private contests must have a password"
            )
            
        updated_contest = await ContestRepository.update_contest(
            db=db, 
            contest_id=contest_id, 
            contest_update=contest_update
        )
        
        return updated_contest
    
    @staticmethod
    async def delete_contest(db: AsyncSession, contest_id: int, current_user_id: int) -> bool:
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Check if user is the contest creator or an admin
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        if contest.creator_id != current_user_id and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this contest"
            )
            
        return await ContestRepository.delete_contest(db=db, contest_id=contest_id)
    
    @staticmethod
    def _validate_state_transition(current_state: str, new_state: str) -> None:
        """Validate that the state transition is allowed"""
        valid_transitions = {
            "open": ["evaluation"],
            "evaluation": ["closed"],
            "closed": []  # No transitions allowed from closed state
        }
        
        if new_state not in valid_transitions.get(current_state, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition from {current_state} to {new_state}"
            )
    
    @staticmethod
    async def check_contest_access(
        db: AsyncSession, 
        contest_id: int, 
        current_user_id: Optional[int] = None, 
        password: Optional[str] = None
    ) -> Contest:
        """Check if user has access to a contest, including password validation for private contests"""
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Public contests are accessible to everyone
        if not contest.is_private:
            return contest
            
        # For private contests, check the provided password
        if contest.is_private:
            # If user is contest creator or admin, allow access without password
            is_admin_user = False
            if current_user_id:
                user_repo = UserRepository(db)
                is_admin_user = await user_repo.is_admin(current_user_id)
            is_creator = current_user_id and contest.creator_id == current_user_id
            
            if is_admin_user or is_creator:
                return contest
                
            # Otherwise, verify the password
            if not password or password != contest.password:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid password for private contest"
                )
                
        return contest
    
    # Text submission methods
    @staticmethod
    async def submit_text_to_contest(
        db: AsyncSession, 
        contest_id: int, 
        submission: TextSubmission, 
        current_user_id: int,
        password: Optional[str] = None
    ) -> ContestText:
        # Check contest access and get contest
        contest = await ContestService.check_contest_access(
            db=db, 
            contest_id=contest_id, 
            current_user_id=current_user_id,
            password=password
        )
        
        # Check if contest is open
        if contest.state != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest is not open for submissions"
            )
            
        # Check if text exists and belongs to the current user
        text_repo = TextRepository(db)
        text = await text_repo.get_text(submission.text_id)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Text with id {submission.text_id} not found"
            )
            
        # Check text ownership (unless user is admin)
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        if text.owner_id != current_user_id and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to submit this text"
            )
            
        # Check contest restrictions
        if contest.author_restrictions:
            # Check if user has already submitted a text
            existing_submissions = await ContestRepository.get_contest_texts(db=db, contest_id=contest_id)
            for sub_item in existing_submissions:
                text_obj = await text_repo.get_text(sub_item.text_id)
                if text_obj and text_obj.owner_id == current_user_id and not is_admin_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Contest only allows one submission per author"
                    )
        
        # If judge restrictions enabled, check if user is a judge
        if contest.judge_restrictions:
            judges = await ContestRepository.get_contest_judges(db=db, contest_id=contest_id)
            if any(judge.judge_id == current_user_id for judge in judges) and not is_admin_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Judges cannot submit texts to this contest"
                )
        
        # Submit the text
        contest_text = await ContestRepository.submit_text_to_contest(
            db=db, 
            contest_id=contest_id, 
            text_id=submission.text_id
        )
        
        if not contest_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text has already been submitted to this contest"
            )
            
        return contest_text
    
    @staticmethod
    async def get_contest_texts(
        db: AsyncSession, 
        contest_id: int, 
        current_user_id: Optional[int] = None,
        password: Optional[str] = None
    ) -> List[ContestText]:
        # Check contest access
        contest = await ContestService.check_contest_access(
            db=db, 
            contest_id=contest_id, 
            current_user_id=current_user_id,
            password=password
        )
        
        # In open contests, only creator and admin can see submissions
        if contest.state == "open":
            is_admin_user = False
            is_creator = False
            if current_user_id:
                user_repo = UserRepository(db)
                is_admin_user = await user_repo.is_admin(current_user_id)
                is_creator = current_user_id and contest.creator_id == current_user_id
            
            if not (is_admin_user or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only contest creator and admins can see submissions in open contests"
                )
        
        return await ContestRepository.get_contest_texts(db=db, contest_id=contest_id)
    
    @staticmethod
    async def remove_text_from_contest(
        db: AsyncSession, 
        contest_id: int, 
        text_id: int, 
        current_user_id: int
    ) -> bool:
        # Get the contest
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Get the text
        text_repo = TextRepository(db)
        text_to_remove = await text_repo.get_text(text_id)
        if not text_to_remove:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Text with id {text_id} not found"
            )
        
        # Check permissions (text owner, contest creator, or admin)
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        is_contest_creator = contest.creator_id == current_user_id
        is_text_owner = text_to_remove.owner_id == current_user_id
        
        if not (is_admin_user or is_contest_creator or is_text_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove this text"
            )
            
        # # Check if contest is not in closed state
        # if contest.state == "closed" and not is_admin_user:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Cannot remove texts from closed contests"
        #     )
            
        # Remove the text
        return await ContestRepository.remove_text_from_contest(
            db=db, 
            contest_id=contest_id, 
            text_id=text_id
        )
    
    # Judge assignment methods
    @staticmethod
    async def assign_judge_to_contest(
        db: AsyncSession, 
        contest_id: int, 
        assignment: JudgeAssignment, 
        current_user_id: int
    ) -> ContestJudge:
        # Get contest
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Check permissions (contest creator or admin)
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        is_creator = contest.creator_id == current_user_id
        
        if not (is_admin_user or is_creator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only contest creator and admins can assign judges"
            )
            
        # Check if user exists
        judge_user = await user_repo.get_by_id(assignment.user_id)
        if not judge_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {assignment.user_id} not found"
            )
            
        # Assign the judge
        contest_judge = await ContestRepository.assign_judge_to_contest(
            db=db, 
            contest_id=contest_id, 
            judge_id=assignment.user_id
        )
        
        if not contest_judge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Judge has already been assigned to this contest"
            )
            
        return contest_judge
    
    @staticmethod
    async def get_contest_judges(
        db: AsyncSession, 
        contest_id: int, 
        current_user_id: Optional[int] = None
    ) -> List[ContestJudge]:
        # Get contest
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Check if user is contest creator, admin, or an assigned judge
        is_admin_user = False
        is_creator = False
        if current_user_id:
            user_repo = UserRepository(db)
            is_admin_user = await user_repo.is_admin(current_user_id)
            is_creator = current_user_id and contest.creator_id == current_user_id
        
        judges = await ContestRepository.get_contest_judges(db=db, contest_id=contest_id)
        is_judge = current_user_id and any(judge.judge_id == current_user_id for judge in judges)
        
        if not (is_admin_user or is_creator or is_judge):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view contest judges"
            )
            
        return judges
    
    @staticmethod
    async def remove_judge_from_contest(
        db: AsyncSession, 
        contest_id: int, 
        judge_id: int, 
        current_user_id: int
    ) -> bool:
        # Get the contest
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        # Check permissions (contest creator or admin)
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        is_creator = contest.creator_id == current_user_id
        
        if not (is_admin_user or is_creator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only contest creator and admins can remove judges"
            )
            
        # Check if judge exists
        judge = await ContestRepository.get_contest_judges(db=db, contest_id=contest_id)
        judge = next((j for j in judge if j.judge_id == judge_id), None)
        
        if not judge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Judge with id {judge_id} not assigned to this contest"
            )
            
        # Check if judge has already voted
        if judge.has_voted and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove a judge who has already voted"
            )
            
        # Remove the judge
        return await ContestRepository.remove_judge_from_contest(
            db=db, 
            contest_id=contest_id, 
            judge_id=judge_id
        )

    @staticmethod
    async def get_contests_where_user_is_judge(db: AsyncSession, judge_id: int, skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get contests where the specified user is a judge."""
        # Validate user exists (optional, but good practice)
        user_repo = UserRepository(db)
        judge_user = await user_repo.get_by_id(judge_id)
        if not judge_user:
            # Or return empty list if judge not existing isn't an error for this context
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {judge_id} not found.")

        return await ContestRepository.get_contests_for_judge(db, judge_id, skip, limit) 