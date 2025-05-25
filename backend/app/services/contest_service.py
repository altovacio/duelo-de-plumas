from typing import List, Optional, Dict, Any, Union
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.contest import (
    ContestCreate, ContestUpdate,  
    TextSubmission, JudgeAssignment, ContestResponse, JudgeAssignmentResponse, ContestTextResponse
)
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.agent_repository import AgentRepository
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.vote import Vote
from app.db.repositories.vote_repository import VoteRepository
from app.schemas.vote import VoteEvaluationResponse

# Import UserModel for author details
from app.db.models.user import User as UserModel
from app.db.models.text import Text as TextModel


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
        
        # Get the complete contest data with creator and counts using the repository method
        contest_data_with_creator = await ContestRepository.get_contest_with_counts(db, created_contest.id)
        
        if not contest_data_with_creator:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created contest data"
            )
        
        # Reflect whether a password is set
        contest_data_with_creator['has_password'] = bool(contest_data_with_creator.get('password'))
        
        # Use model_validate to create the Pydantic response model instance
        return ContestResponse.model_validate(contest_data_with_creator)
    
    @staticmethod
    async def get_contests(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        current_user_id: Optional[int] = None,
        creator: Optional[Union[int, str]] = None  # Can be 'me', user_id (int), or user_id (str)
    ) -> List[ContestResponse]:
        creator_id_to_filter: Optional[Union[int, str]] = None
        if creator == "me" and current_user_id is not None:
            creator_id_to_filter = current_user_id
        elif creator is not None:
            creator_id_to_filter = creator
        # If creator is something else, or current_user_id is None, no creator filter is applied unless explicitly passed
        # This maintains existing behavior for general contest listing if creator != 'me'

        contests_orm = await ContestRepository.get_contests(
            db=db, 
            skip=skip, 
            limit=limit, 
            status=status,
            current_user_id=current_user_id, # Still passed for any other internal uses it might have
            creator_id=creator_id_to_filter  # Pass the determined creator_id for filtering
        )
        
        response_list = []
        for contest_orm in contests_orm:
            # Fetch details including counts for each contest
            # This uses the already corrected get_contest_with_counts from the repository
            contest_data_with_counts = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_orm.id)
            if contest_data_with_counts:
                # Reflect whether a password is set on each contest
                contest_data_with_counts['has_password'] = bool(contest_data_with_counts.get('password'))
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
                    "user_judge_id": judge_orm.user_judge_id,
                    "agent_judge_id": judge_orm.agent_judge_id,
                    "assignment_date": judge_orm.assignment_date,
                    "has_voted": judge_orm.has_voted
                })
        
        final_result_dict = raw_result_dict.copy()
        final_result_dict["judges"] = transformed_judges_list
        
        # Reflect whether a password is set
        final_result_dict['has_password'] = bool(final_result_dict.get('password'))
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
        
        # Prepare a mutable copy of contest_update data for potential modification
        update_data_dict = contest_update.model_dump(exclude_unset=True)
        # If setting to public, explicitly clear the password so it is removed in the DB
        if update_data_dict.get('is_private') is False:
            update_data_dict['password'] = None

        # Validate status transition and ensure status is lowercase before saving
        if "status" in update_data_dict and update_data_dict["status"] != contest.status:
            original_new_status = update_data_dict["status"]
            lowercase_new_status = original_new_status.lower()
            ContestService._validate_status_transition(contest.status, lowercase_new_status) # Validate with lowercase
            update_data_dict["status"] = lowercase_new_status # Store lowercase status

        # Create a new ContestUpdate instance with potentially modified (lowercased) status
        # This ensures that the repository receives the standardized status.
        final_contest_update = ContestUpdate(**update_data_dict)
            
        # Validate that private contests have a password
        is_private_after_update = final_contest_update.is_private if final_contest_update.is_private is not None else contest.is_private
        password_after_update = final_contest_update.password if final_contest_update.password is not None else contest.password

        if is_private_after_update and not password_after_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private contests must have a password"
            )
            
        updated_contest_orm = await ContestRepository.update_contest(
            db=db, 
            contest_id=contest_id, 
            contest_update=final_contest_update # Pass the ContestUpdate with lowercase status
        )
        
        # Check if the contest is now closed and trigger result computation
        if updated_contest_orm and updated_contest_orm.status.lower() == "closed":
            await VoteRepository.calculate_contest_results(db, contest_id)
            # Fetch the updated contest data again AFTER results computation to ensure response reflects ranks
            # This is important because the contest_orm might be stale regarding submission ranks
            updated_contest_data = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_id)
        else:
            # If not newly closed or update failed, get data as before
             updated_contest_data = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_id)

        if not updated_contest_orm:
            # This case should ideally not happen if get_contest succeeded earlier
            # but handle defensively.
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # Or 500 Internal Server Error
                detail=f"Contest with id {contest_id} not found after update attempt."
            )
        
        # Reflect whether a password is set
        updated_contest_data['has_password'] = bool(updated_contest_data.get('password'))
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
    def _validate_status_transition(current_status: str, new_status: str) -> None:
        """Validate that the status transition is allowed"""
        valid_transitions = {
            "open": ["evaluation", "closed"],
            "evaluation": ["closed", "open"],
            "closed": ["open", "evaluation"]  # No transitions allowed from closed state
        }
        
        processed_new_status = new_status.lower() # Convert to lowercase
        if processed_new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}"
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
        if contest.status != "open":
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

        if assignment.user_judge_id is not None:
            judge_user = await user_repo.get_by_id(assignment.user_judge_id)
            if not judge_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {assignment.user_judge_id} not found to assign as judge."
                )
            user_judge_id_to_assign = judge_user.id
            # TODO: Consider contest.judge_restrictions for user authors

        elif assignment.agent_judge_id:
            # Verify agent exists using the static method and correct name
            agent_to_assign = await AgentRepository.get_agent_by_id(db, assignment.agent_judge_id)
            if not agent_to_assign:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent with id {assignment.agent_judge_id} not found")
            # Check if the agent is public OR if it belongs to the current_user_id
            if not agent_to_assign.is_public and agent_to_assign.owner_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only assign your own private agents or public agents"
                )
            agent_judge_id_to_assign = assignment.agent_judge_id # Correct variable assignment
            # TODO: Consider contest.judge_restrictions for agent owners
        else:
            # This should ideally be caught by Pydantic validation in the schema itself
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assignment: Either user_judge_id or agent_judge_id must be provided."
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
            "user_judge_id": assigned_judge_entry.user_judge_id,
            "agent_judge_id": assigned_judge_entry.agent_judge_id,
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
    async def get_contests_by_creator(db: AsyncSession, creator_id: int, skip: int = 0, limit: int = 100) -> List[Contest]:
        """Get contests created by the specified user."""
        # Validate user exists (optional, but good practice)
        user_repo = UserRepository(db)
        creator_user = await user_repo.get_by_id(creator_id)
        if not creator_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {creator_id} not found.")

        stmt = select(Contest).filter(Contest.creator_id == creator_id).order_by(Contest.id.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_contests_where_user_is_judge(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get contests where the specified user is a judge."""
        # Validate user exists (optional, but good practice)
        user_repo = UserRepository(db)
        judge_user = await user_repo.get_by_id(user_id)
        if not judge_user:
            # Or return empty list if judge not existing isn't an error for this context
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found.")

        return await ContestRepository.get_contests_for_judge(db, user_judge_id=user_id, skip=skip, limit=limit)

    @staticmethod
    async def get_contests_where_user_is_author(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get contests where the specified user has submitted texts as an author."""
        # Validate user exists (optional, but good practice)
        user_repo = UserRepository(db)
        author_user = await user_repo.get_by_id(user_id)
        if not author_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found.")

        return await ContestRepository.get_contests_for_author(db, user_id=user_id, skip=skip, limit=limit)

    @staticmethod
    async def get_contest_submissions(
        db: AsyncSession,
        contest_id: int,
        current_user_id: Optional[int] = None,
        password: Optional[str] = None
    ) -> List[ContestTextResponse]:
        """
        Get all text submissions for a contest with proper masking based on contest status.
        
        For open contests, only creator and admins can see submissions
        For evaluation contests, submissions are visible but author/owner are masked
        For closed contests, all details are visible, including evaluations.
        """
        contest = await ContestService.check_contest_access(
            db=db,
            contest_id=contest_id,
            current_user_id=current_user_id,
            password=password
        )
        
        if contest.status.lower() == "open":
            if current_user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            user_repo = UserRepository(db)
            is_admin_user = await user_repo.is_admin(current_user_id)
            is_creator = contest.creator_id == current_user_id
            if not (is_admin_user or is_creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Submissions are not visible to participants while the contest is open."
                )
        
        contest_texts = await ContestRepository.get_contest_texts(db=db, contest_id=contest_id)
        text_repo = TextRepository(db)
        # Fetch all votes for the contest once if it's closed to optimize DB calls
        all_contest_votes: List[Vote] = []
        if contest.status.lower() == "closed":
            all_contest_votes = await VoteRepository.get_votes_by_contest(db=db, contest_id=contest_id)

        results = []
        for ct in contest_texts:
            text = await text_repo.get_text(ct.text_id)
            if not text:
                continue

            author_name = text.author
            owner_id_val = text.owner_id
            submission_evaluations: List[VoteEvaluationResponse] = [] # Ensure type

            contest_state = contest.status.lower()
            # Mask or reveal owner/author based on contest state
            if contest_state == "evaluation":
                author_name = "[Hidden]"
                owner_id_val = None
            # For "open" state, author and owner are revealed only to creator/admin, handled by initial check.
            # For "closed" state, author and owner are revealed to all with access.
            
            if contest_state == "closed":
                text_specific_votes = [v for v in all_contest_votes if v.text_id == ct.text_id]
                for vote_obj in text_specific_votes:
                    judge_identifier_str = f"Judge (ID: {vote_obj.contest_judge_id})" # Default/fallback
                    if vote_obj.contest_judge_id:
                        contest_judge_entry = await ContestRepository.get_contest_judge_by_id(db, vote_obj.contest_judge_id)
                        if contest_judge_entry:
                            if contest_judge_entry.user_judge_id:
                                user_repo = UserRepository(db)
                                user_judge = await user_repo.get_by_id(contest_judge_entry.user_judge_id)
                                if user_judge:
                                    judge_identifier_str = user_judge.username
                                else:
                                    judge_identifier_str = "Unknown User Judge"
                            elif contest_judge_entry.agent_judge_id:
                                agent_judge = await AgentRepository.get_agent_by_id(db, contest_judge_entry.agent_judge_id)
                                if agent_judge:
                                    judge_identifier_str = agent_judge.name
                                else:
                                    judge_identifier_str = "Unknown Agent Judge"
                        else:
                            judge_identifier_str = "ContestJudge entry not found"
                    
                    submission_evaluations.append(
                        VoteEvaluationResponse(
                            comment=vote_obj.comment,
                            judge_identifier=judge_identifier_str,
                            text_place=vote_obj.text_place
                        )
                    )
            
            # Construct the response dictionary for the current submission
            submission_data_dict = {
                "id": ct.id,
                "contest_id": ct.contest_id,
                "text_id": text.id,
                "submission_date": ct.submission_date,
                "title": text.title,
                "content": text.content,
                "author": author_name,
                "owner_id": owner_id_val,
                "ranking": ct.ranking,
                "total_points": ct.total_points,
                # Only include evaluations if the contest is closed and evaluations were processed
                "evaluations": submission_evaluations if contest_state == "closed" and submission_evaluations else None
            }
            results.append(ContestTextResponse.model_validate(submission_data_dict))
            
        return results

    @classmethod
    async def get_all_my_submissions(
        cls, db: AsyncSession, current_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ContestTextResponse]:
        """
        Retrieves all submissions made by the current_user_id across all contests,
        ordered by submission date (most recent first).
        """
        stmt = (
            select(
                ContestText,  # The whole submission ORM object
                TextModel,    # The whole text ORM object
                UserModel,    # The user ORM object for the owner
                Contest       # Include the contest to check status
            )
            .join(TextModel, ContestText.text_id == TextModel.id)
            .join(UserModel, TextModel.owner_id == UserModel.id)
            .join(Contest, ContestText.contest_id == Contest.id)
            .where(TextModel.owner_id == current_user_id)  # Filter by the text's owner
            .order_by(ContestText.submission_date.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        raw_results = result.all()  # List of tuples: (ContestText_instance, TextModel_instance, UserModel_instance, Contest_instance)

        response_list = []
        for ct_orm, text_orm, owner_orm, contest_orm in raw_results:
            # Use the text's author field, which is user-provided text
            author_name = text_orm.author
            
            submission_evaluations: List[VoteEvaluationResponse] = []
            
            # Include evaluations if contest is closed
            if contest_orm.status.lower() == "closed":
                # Fetch votes for this specific text in this contest
                text_votes = await VoteRepository.get_votes_by_contest(db=db, contest_id=ct_orm.contest_id)
                text_specific_votes = [v for v in text_votes if v.text_id == ct_orm.text_id]
                
                for vote_obj in text_specific_votes:
                    judge_identifier_str = f"Judge (ID: {vote_obj.contest_judge_id})" # Default/fallback
                    if vote_obj.contest_judge_id:
                        contest_judge_entry = await ContestRepository.get_contest_judge_by_id(db, vote_obj.contest_judge_id)
                        if contest_judge_entry:
                            if contest_judge_entry.user_judge_id:
                                user_repo = UserRepository(db)
                                user_judge = await user_repo.get_by_id(contest_judge_entry.user_judge_id)
                                if user_judge:
                                    judge_identifier_str = user_judge.username
                                else:
                                    judge_identifier_str = "Unknown User Judge"
                            elif contest_judge_entry.agent_judge_id:
                                agent_judge = await AgentRepository.get_agent_by_id(db, contest_judge_entry.agent_judge_id)
                                if agent_judge:
                                    judge_identifier_str = agent_judge.name
                                else:
                                    judge_identifier_str = "Unknown Agent Judge"
                        else:
                            judge_identifier_str = "ContestJudge entry not found"
                    
                    submission_evaluations.append(
                        VoteEvaluationResponse(
                            comment=vote_obj.comment,
                            judge_identifier=judge_identifier_str,
                            text_place=vote_obj.text_place
                        )
                    )
            
            response_item = ContestTextResponse(
                id=ct_orm.id,
                contest_id=ct_orm.contest_id,
                text_id=ct_orm.text_id,
                submission_date=ct_orm.submission_date,
                title=text_orm.title,
                content=text_orm.content,
                author=author_name,
                owner_id=text_orm.owner_id,
                ranking=ct_orm.ranking,
                total_points=ct_orm.total_points,
                evaluations=submission_evaluations if contest_orm.status.lower() == "closed" and submission_evaluations else None
            )
            response_list.append(response_item)
        
        return response_list

    @classmethod
    async def get_my_submissions_for_contest(
        cls, db: AsyncSession, contest_id: int, current_user_id: int
    ) -> List[ContestTextResponse]:
        """
        Retrieves all submissions made by the current_user_id for the given contest_id.
        """
        # Get contest to check status
        contest = await ContestService.get_contest(db=db, contest_id=contest_id)
        
        stmt = (
            select(
                ContestText, # The whole submission ORM object (ContestText model)
                TextModel,     # The whole text ORM object
                UserModel      # The user ORM object for the owner
            )
            .join(TextModel, ContestText.text_id == TextModel.id)
            .join(UserModel, TextModel.owner_id == UserModel.id) # Join to get owner details
            .where(ContestText.contest_id == contest_id)
            .where(TextModel.owner_id == current_user_id) # Filter by the text's owner, who is the current user
            .order_by(ContestText.submission_date.desc())
        )
        
        result = await db.execute(stmt)
        raw_results = result.all() # List of tuples: (ContestText_instance, TextModel_instance, UserModel_instance)

        # Fetch all votes for the contest if it's closed to include evaluations
        all_contest_votes: List[Vote] = []
        if contest.status.lower() == "closed":
            all_contest_votes = await VoteRepository.get_votes_by_contest(db=db, contest_id=contest_id)

        response_list = []
        for ct_orm, text_orm, owner_orm in raw_results:
            # Use the text's author field, which is user-provided text
            author_name = text_orm.author
            
            submission_evaluations: List[VoteEvaluationResponse] = []
            
            # Include evaluations if contest is closed
            if contest.status.lower() == "closed":
                text_specific_votes = [v for v in all_contest_votes if v.text_id == ct_orm.text_id]
                for vote_obj in text_specific_votes:
                    judge_identifier_str = f"Judge (ID: {vote_obj.contest_judge_id})" # Default/fallback
                    if vote_obj.contest_judge_id:
                        contest_judge_entry = await ContestRepository.get_contest_judge_by_id(db, vote_obj.contest_judge_id)
                        if contest_judge_entry:
                            if contest_judge_entry.user_judge_id:
                                user_repo = UserRepository(db)
                                user_judge = await user_repo.get_by_id(contest_judge_entry.user_judge_id)
                                if user_judge:
                                    judge_identifier_str = user_judge.username
                                else:
                                    judge_identifier_str = "Unknown User Judge"
                            elif contest_judge_entry.agent_judge_id:
                                agent_judge = await AgentRepository.get_agent_by_id(db, contest_judge_entry.agent_judge_id)
                                if agent_judge:
                                    judge_identifier_str = agent_judge.name
                                else:
                                    judge_identifier_str = "Unknown Agent Judge"
                        else:
                            judge_identifier_str = "ContestJudge entry not found"
                    
                    submission_evaluations.append(
                        VoteEvaluationResponse(
                            comment=vote_obj.comment,
                            judge_identifier=judge_identifier_str,
                            text_place=vote_obj.text_place
                        )
                    )
            
            response_item = ContestTextResponse(
                id=ct_orm.id, # This is submission_id
                contest_id=ct_orm.contest_id,
                text_id=ct_orm.text_id,
                submission_date=ct_orm.submission_date,
                title=text_orm.title,
                content=text_orm.content,
                author=author_name, # Use the actual author field from the text
                owner_id=text_orm.owner_id,
                ranking=ct_orm.ranking,
                total_points=ct_orm.total_points,
                evaluations=submission_evaluations if contest.status.lower() == "closed" and submission_evaluations else None
            )
            response_list.append(response_item)
        
        return response_list

 