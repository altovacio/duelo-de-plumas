from typing import List, Optional
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

router = APIRouter()


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
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    """
    Get list of contests with optional filtering.
    All users (authenticated or visitor) see all contests listed.
    Access to details of private contests is handled by the GET /{contest_id} endpoint.
    """
    user_id = current_user.id if current_user else None
    return await ContestService.get_contests(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        current_user_id=user_id
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


@router.get("/{contest_id}/submissions", response_model=List[ContestTextResponse])
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
    current_user: Optional[UserModel] = Depends(get_current_user)
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
    
    return [
        JudgeAssignmentResponse(
            contest_id=cj.contest_id,
            judge_id=cj.judge_id,
            assignment_date=cj.assignment_date
        ) for cj in contest_judges
    ]


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