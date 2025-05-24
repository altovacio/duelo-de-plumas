from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.db.database import get_db
from app.api.routes.auth import get_current_user, get_optional_current_user
from app.schemas.contest import (
    ContestCreate, ContestResponse, ContestUpdate, ContestDetailResponse,
    TextSubmission, TextSubmissionResponse, JudgeAssignment, JudgeAssignmentResponse,
    ContestTextResponse
)
from app.db.models.user import User as UserModel
from app.services.contest_service import ContestService

router = APIRouter(tags=["contests"])


@router.post("/", response_model=ContestResponse, status_code=status.HTTP_201_CREATED)
async def create_contest(
    contest: ContestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new contest
    """
    return await ContestService.create_contest(db=db, contest=contest, creator_id=current_user.id)


@router.get("/", response_model=List[ContestResponse])
async def get_contests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter contests by status (e.g., open, closed, evaluation)"),
    creator: Optional[Union[int, str]] = Query(None, description="Filter contests by creator. Use 'me' for current user's contests."),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    """
    Get list of contests with optional filtering.
    If 'creator=me' is passed, only contests created by the current user are returned.
    Otherwise, all users (authenticated or visitor) see all contests listed (unless other filters apply).
    Access to details of private contests is handled by the GET /{contest_id} endpoint.
    """
    user_id = current_user.id if current_user else None
    return await ContestService.get_contests(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        current_user_id=user_id,
        creator=creator
    )


@router.get("/my-submissions/", response_model=List[ContestTextResponse])
async def get_all_my_submissions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # Requires authenticated user
):
    """
    Get all text submissions made by the current authenticated user across all contests.
    This endpoint provides a complete view of all the user's contest participation.
    """
    return await ContestService.get_all_my_submissions(
        db=db,
        current_user_id=current_user.id,
        skip=skip,
        limit=limit
    )


@router.get("/{contest_id}", response_model=ContestDetailResponse)
async def get_contest(
    contest_id: int,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    """
    Get contest details including participant and text counts
    
    For private contests, provide the password unless you're the creator or admin
    """
    user_id = current_user.id if current_user else None
    await ContestService.check_contest_access(
        db=db,
        contest_id=contest_id,
        current_user_id=user_id,
        password=password
    )
    
    # Service now returns a dictionary with all required fields and counts
    result_dict = await ContestService.get_contest_detail(db=db, contest_id=contest_id)

    # Validate the dictionary directly using Pydantic
    try:
        response = ContestDetailResponse(**result_dict)
    except ValidationError as e:
        print(f"ERROR: Pydantic validation failed for contest {contest_id} dict: {e}") 
        print(f"Data passed: {result_dict}") # Log the data that failed validation
        raise HTTPException(status_code=500, detail="Internal server error validating response data")

    return response


@router.put("/{contest_id}", response_model=ContestResponse)
async def update_contest(
    contest_id: int,
    contest_update: ContestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update contest details
    
    Only the contest creator or admin can update a contest
    """
    return await ContestService.update_contest(
        db=db,
        contest_id=contest_id,
        contest_update=contest_update,
        current_user_id=current_user.id
    )


@router.delete("/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contest(
    contest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a contest
    
    Only the contest creator or admin can delete a contest
    When a contest is deleted, associated votes are removed but texts are preserved
    """
    await ContestService.delete_contest(
        db=db,
        contest_id=contest_id,
        current_user_id=current_user.id
    )
    return None


# Text submission endpoints
@router.post("/{contest_id}/submissions/", response_model=TextSubmissionResponse)
async def submit_text_to_contest(
    contest_id: int,
    submission: TextSubmission,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Submit a text to a contest
    
    For private contests, provide the password unless you're the creator or admin
    """
    contest_text = await ContestService.submit_text_to_contest(
        db=db,
        contest_id=contest_id,
        submission=submission,
        current_user_id=current_user.id,
        password=password
    )
    
    # Return the response including the submission ID
    return TextSubmissionResponse(
        submission_id=contest_text.id,
        contest_id=contest_text.contest_id,
        text_id=contest_text.text_id,
        submission_date=contest_text.submission_date
    )


@router.get("/{contest_id}/submissions/", response_model=List[ContestTextResponse])
async def get_contest_submissions(
    contest_id: int,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    """
    Get all text submissions for a contest
    
    For private contests, provide the password unless you're the creator or admin
    For open contests, only the creator and admins can see submissions
    For evaluation/closed contests, anyone with access can see submissions with full details
    """
    user_id = current_user.id if current_user else None
    return await ContestService.get_contest_submissions(
        db=db,
        contest_id=contest_id,
        current_user_id=user_id,
        password=password
    )


@router.get("/{contest_id}/my-submissions/", response_model=List[ContestTextResponse])
async def get_my_contest_submissions(
    contest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # Requires authenticated user
):
    """
    Get all text submissions made by the current authenticated user for a specific contest.
    This allows users to see their own submissions even in open contests where general
    submission visibility is restricted to creators/admins.
    """
    # First, ensure the contest exists and the user could potentially access it.
    # (Optional: A light check, or rely on contest_id being valid from prior navigation)
    # For this focused endpoint, we primarily care about fetching user's own items.
    # A more robust check_contest_access without password might be used if strictness is needed here too.
    
    # The main logic will be in the service layer
    my_submissions = await ContestService.get_my_submissions_for_contest(
        db=db,
        contest_id=contest_id,
        current_user_id=current_user.id
    )
    return my_submissions


@router.delete("/{contest_id}/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_submission_from_contest(
    contest_id: int,
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Remove a text submission from a contest using the submission ID.
    
    Can be done by:
    - The text owner (owner of the text submitted)
    - The contest creator
    - An admin
    """
    await ContestService.remove_submission(
        db=db,
        contest_id=contest_id,
        submission_id=submission_id,
        current_user_id=current_user.id
    )
    return None


# Judge assignment endpoints
@router.post("/{contest_id}/judges", response_model=JudgeAssignmentResponse)
async def assign_judge_to_contest(
    contest_id: int,
    assignment: JudgeAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Assign a judge (user or AI agent) to a contest.
    
    Only the contest creator or admin can assign judges.
    """
    contest_judge_entry = await ContestService.assign_judge_to_contest(
        db=db,
        contest_id=contest_id,
        assignment=assignment,
        current_user_id=current_user.id
    )
    
    # The service now returns a JudgeAssignmentResponse directly
    return contest_judge_entry


@router.get("/{contest_id}/judges", response_model=List[JudgeAssignmentResponse])
async def get_contest_judges(
    contest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    """
    Get all judges assigned to a contest
    
    Accessible to:
    - The contest creator
    - Assigned judges
    - Admins
    """
    user_id = current_user.id if current_user else None
    contest_judges = await ContestService.get_contest_judges(
        db=db,
        contest_id=contest_id,
        current_user_id=user_id
    )
    
    # Import repositories to get additional judge information
    from app.db.repositories.user_repository import UserRepository
    from app.db.repositories.agent_repository import AgentRepository
    
    user_repo = UserRepository(db)
    
    result = []
    for cj in contest_judges:
        judge_response = JudgeAssignmentResponse(
            id=cj.id,
            contest_id=cj.contest_id,
            user_judge_id=cj.user_judge_id,
            agent_judge_id=cj.agent_judge_id,
            assignment_date=cj.assignment_date,
            has_voted=cj.has_voted
        )
        
        # Populate additional fields based on judge type
        if cj.user_judge_id:
            # Human judge - get user details
            user_judge = await user_repo.get_by_id(cj.user_judge_id)
            if user_judge:
                judge_response.user_judge_name = user_judge.username
                judge_response.user_judge_email = user_judge.email
        elif cj.agent_judge_id:
            # AI judge - get agent details
            agent_judge = await AgentRepository.get_agent_by_id(db, cj.agent_judge_id)
            if agent_judge:
                judge_response.agent_judge_name = agent_judge.name
                # Note: model is execution-specific, not stored on the agent itself
        
        result.append(judge_response)
    
    return result


@router.delete("/{contest_id}/judges/{judge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_judge_from_contest(
    contest_id: int,
    judge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Remove a judge from a contest
    
    Only the contest creator or admin can remove judges
    Cannot remove a judge who has already voted (unless you're an admin)
    """
    await ContestService.remove_judge_from_contest(
        db=db,
        contest_id=contest_id,
        judge_id=judge_id,
        current_user_id=current_user.id
    )
    return None 