from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.contest import (
    ContestCreate, ContestUpdate,  
    TextSubmission, JudgeAssignment, ContestResponse, JudgeAssignmentResponse
)
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.agent_repository import AgentRepository
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge


class ContestService:
    @staticmethod
    async def create_contest(db: AsyncSession, contest: ContestCreate, creator_id: int) -> ContestResponse:
        # Validate that private contests have a password
        if contest.is_private and not contest.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private contests must have a password"
            )
            
        created_contest = await ContestRepository.create_contest(db, contest, creator_id)
        
        # Manually construct the response including counts initialized to 0
        response_data = created_contest.__dict__.copy() # Get ORM attributes
        response_data['participant_count'] = 0
        response_data['text_count'] = 0
        
        # Use model_validate to create the Pydantic response model instance
        return ContestResponse.model_validate(response_data)
    
    @staticmethod
    async def get_contests(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        state: Optional[str] = None,
        current_user_id: Optional[int] = None
    ) -> List[ContestResponse]:
        contests_orm = await ContestRepository.get_contests(
            db=db, 
            skip=skip, 
            limit=limit, 
            state=state,
            current_user_id=current_user_id
        )
        
        response_list = []
        for contest_orm in contests_orm:
            # Fetch details including counts for each contest
            # This uses the already corrected get_contest_with_counts from the repository
            contest_data_with_counts = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_orm.id)
            if contest_data_with_counts:
                response_list.append(ContestResponse.model_validate(contest_data_with_counts))
            else:
                # This case should ideally not happen if contest_orm.id is valid
                # Handle defensively: either skip or raise an error
                # For now, let's log and skip, or one could raise an internal error
                print(f"Warning: Could not retrieve details for contest id {contest_orm.id} in get_contests list.")
                # If strictness is required, one might raise HTTPException here

        return response_list
    
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
        # Repository method now returns a dictionary with contest data and counts
        raw_result_dict = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_id)
        if not raw_result_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest with id {contest_id} not found"
            )
        
        # Transform judge ORM objects to dictionaries matching JudgeAssignmentResponse
        transformed_judges_list = []
        if "judges" in raw_result_dict and raw_result_dict["judges"]:
            for judge_orm in raw_result_dict["judges"]:
                transformed_judges_list.append({
                    "id": judge_orm.id,
                    "contest_id": judge_orm.contest_id,
                    "user_id": judge_orm.user_judge_id, # Map from user_judge_id
                    "agent_id": judge_orm.agent_judge_id, # Map from agent_judge_id
                    "assignment_date": judge_orm.assignment_date,
                    "has_voted": judge_orm.has_voted
                })
        
        final_result_dict = raw_result_dict.copy()
        final_result_dict["judges"] = transformed_judges_list
        
        return final_result_dict
    
    @staticmethod
    async def update_contest(
        db: AsyncSession, 
        contest_id: int, 
        contest_update: ContestUpdate, 
        current_user_id: int
    ) -> ContestResponse:
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
        
        if not updated_contest:
            # This case should ideally not happen if get_contest succeeded earlier
            # but handle defensively.
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # Or 500 Internal Server Error
                detail=f"Contest with id {contest_id} not found after update attempt."
            )
        
        # Fetch the updated contest data including counts and judges
        updated_contest_data = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_id)
        
        if not updated_contest_data:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # Or 500 Internal Server Error
                detail=f"Could not retrieve contest details for id {contest_id} after update."
            )
            
        # Validate and return as ContestResponse
        # Note: get_contest_with_counts returns a dict with judges, 
        # but ContestResponse doesn't expect judges. Pydantic handles extra fields by default.
        return ContestResponse.model_validate(updated_contest_data)
    
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
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Contest only allows one submission per author"
                    )
        
        # If judge restrictions enabled, check if user is a judge
        if contest.judge_restrictions:
            judges = await ContestRepository.get_contest_judges(db=db, contest_id=contest_id)
            if any(judge.user_judge_id == current_user_id for judge in judges) and not is_admin_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
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
        
        # For open contests, only the creator and admins can see submissions details
        # (This method returns ContestText objects, details masking for actual content/author should happen in router/schema if needed)
        if contest.state == "open":
            is_admin_user = False
            if current_user_id:
                user_repo = UserRepository(db)
                is_admin_user = await user_repo.is_admin(current_user_id)
            
            is_creator = current_user_id and contest.creator_id == current_user_id
            
            if not (is_admin_user or is_creator):
                # Non-creator/non-admin cannot view submissions list in 'open' state
                # Or, return an empty list if preferred over raising an error for list endpoint
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Submissions are not visible to participants while the contest is open."
                )
        
        # For 'evaluation' or 'closed' states, all who can access contest can see submissions
        # (masking of author/owner handled by specific response schemas if needed)
        return await ContestRepository.get_contest_texts(db=db, contest_id=contest_id)
    
    @staticmethod
    async def remove_submission(
        db: AsyncSession, 
        contest_id: int, 
        submission_id: int, 
        current_user_id: int
    ) -> bool:
        """Removes a text submission from a contest using the submission ID."""
        # Get the specific submission (ContestText record)
        submission_record = await ContestRepository.get_submission_by_id(db, submission_id)
        
        if not submission_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission with id {submission_id} not found"
            )
        
        # Verify the submission belongs to the specified contest
        if submission_record.contest_id != contest_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Or 404 if we want to hide its existence on other contests
                detail=f"Submission {submission_id} does not belong to contest {contest_id}"
            )

        # Get the contest for creator check
        contest = await ContestService.get_contest(db=db, contest_id=contest_id) # Already checks if contest exists

        # Get the actual text for owner check
        text_repo = TextRepository(db)
        text = await text_repo.get_text(submission_record.text_id) # Use text_id from submission_record
        
        if not text: # Should not happen if submission_record.text_id is valid
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Text associated with submission {submission_id} (Text ID: {submission_record.text_id}) not found"
            )
        
        # Check permissions: current user must be text owner, contest creator, or an admin
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        is_text_owner = text.owner_id == current_user_id
        is_contest_creator = contest.creator_id == current_user_id
        
        if not (is_text_owner or is_contest_creator or is_admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove this submission from the contest"
            )
            
        # Delete the submission using its ID
        deleted = await ContestRepository.delete_submission(db, submission_id)
        if not deleted:
             # This might happen if it was deleted in a race condition
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to delete submission {submission_id}, it might have been already removed."
            )
        return True
    
    # Judge assignment methods
    @staticmethod
    async def assign_judge_to_contest(
        db: AsyncSession, 
        contest_id: int, 
        assignment: JudgeAssignment,
        current_user_id: int
    ) -> JudgeAssignmentResponse:
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        user_repo = UserRepository(db)
        is_admin_user = await user_repo.is_admin(current_user_id)
        if contest.creator_id != current_user_id and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to assign judges to this contest"
            )

        user_judge_id_to_assign: Optional[int] = None
        agent_judge_id_to_assign: Optional[int] = None

        if assignment.user_id is not None:
            judge_user = await user_repo.get_by_id(assignment.user_id)
            if not judge_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {assignment.user_id} not found to assign as judge."
                )
            user_judge_id_to_assign = judge_user.id
            # TODO: Consider contest.judge_restrictions for user authors

        elif assignment.agent_id:
            # Verify agent exists using the static method and correct name
            agent_to_assign = await AgentRepository.get_agent_by_id(db, assignment.agent_id)
            if not agent_to_assign:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent with id {assignment.agent_id} not found")
            # Check if the agent is public OR if it belongs to the current_user_id
            if not agent_to_assign.is_public and agent_to_assign.owner_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only assign your own private agents or public agents"
                )
            agent_judge_id_to_assign = assignment.agent_id # Correct variable assignment
            # TODO: Consider contest.judge_restrictions for agent owners
        else:
            # This should ideally be caught by Pydantic validation in the schema itself
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assignment: Either user_id or agent_id must be provided."
            )

        # Call updated repository method (to be created/updated in ContestRepository)
        assigned_judge_entry = await ContestRepository.assign_judge_to_contest(
            db=db, 
            contest_id=contest_id, 
            user_judge_id=user_judge_id_to_assign,
            agent_judge_id=agent_judge_id_to_assign
        )
        
        if not assigned_judge_entry:
            judge_type = "User" if user_judge_id_to_assign else "Agent"
            judge_id_val = user_judge_id_to_assign if user_judge_id_to_assign else agent_judge_id_to_assign
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{judge_type} with id {judge_id_val} is already assigned as a judge to this contest or another error occurred."
            )
            
        # Manually construct response data from ORM object
        response_data = {
            "id": assigned_judge_entry.id,
            "contest_id": assigned_judge_entry.contest_id,
            "user_id": assigned_judge_entry.user_judge_id,  # Map from user_judge_id
            "agent_id": assigned_judge_entry.agent_judge_id, # Map from agent_judge_id
            "assignment_date": assigned_judge_entry.assignment_date,
            "has_voted": assigned_judge_entry.has_voted,
        }
        return JudgeAssignmentResponse.model_validate(response_data)
    
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
        # Corrected check for human judge
        is_judge = current_user_id and any(judge.user_judge_id == current_user_id for judge in judges)
        
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
        judge_id: int, # This is the ContestJudge.id, the ID of the assignment entry
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
            
        # Find the specific judge assignment entry by its ID (judge_id here is ContestJudge.id)
        # This requires fetching the specific ContestJudge entry to check its has_voted status.
        # We can do this by selecting the specific entry by its ID.
        stmt = select(ContestJudge).where(ContestJudge.id == judge_id, ContestJudge.contest_id == contest_id)
        result = await db.execute(stmt)
        judge_assignment_entry = result.scalar_one_or_none()
        
        if not judge_assignment_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Judge assignment entry with id {judge_id} not found for this contest"
            )
            
        # Check if judge has already voted
        if judge_assignment_entry.has_voted and not is_admin_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove a judge who has already voted"
            )
            
        # Remove the judge assignment by its ID
        return await ContestRepository.remove_judge_from_contest(
            db=db, 
            contest_id=contest_id, 
            contest_judge_id=judge_id # Pass the ContestJudge.id
        )

    @staticmethod
    async def get_contests_where_user_is_judge(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get contests where the specified user is a judge."""
        # Validate user exists (optional, but good practice)
        user_repo = UserRepository(db)
        judge_user = await user_repo.get_by_id(user_id)
        if not judge_user:
            # Or return empty list if judge not existing isn't an error for this context
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found.")

        return await ContestRepository.get_contests_for_judge(db, user_judge_id=user_id, skip=skip, limit=limit) 