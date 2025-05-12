from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.schemas.contest import (
    ContestCreate, ContestResponse, ContestUpdate, ContestDetailResponse,
    TextSubmission, TextSubmissionResponse, JudgeAssignment, JudgeAssignmentResponse
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
    state: Optional[str] = None,
    is_private: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """
    Get list of contests with optional filtering
    """
    return await ContestService.get_contests(
        db=db,
        skip=skip,
        limit=limit,
        state=state,
        is_private=is_private
    )


@router.get("/{contest_id}", response_model=ContestDetailResponse)
async def get_contest(
    contest_id: int,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
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
    
    result = await ContestService.get_contest_detail(db=db, contest_id=contest_id)

    # Create response
    contest_db_model = result["contest"]
    response_data = contest_db_model.__dict__.copy()
    response_data.update({
        "participant_count": result["participant_count"],
        "text_count": result["text_count"]
    })
    return ContestDetailResponse(**response_data)


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
@router.post("/{contest_id}/submissions", response_model=TextSubmissionResponse)
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
    
    return TextSubmissionResponse(
        contest_id=contest_text.contest_id,
        text_id=contest_text.text_id,
        submission_date=contest_text.submission_date
    )


@router.get("/{contest_id}/submissions", response_model=List[TextSubmissionResponse])
async def get_contest_submissions(
    contest_id: int,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user)
):
    """
    Get all text submissions for a contest
    
    For private contests, provide the password unless you're the creator or admin
    For open contests, only the creator and admins can see submissions
    """
    user_id = current_user.id if current_user else None
    contest_texts = await ContestService.get_contest_texts(
        db=db,
        contest_id=contest_id,
        current_user_id=user_id,
        password=password
    )
    
    return [
        TextSubmissionResponse(
            contest_id=ct.contest_id,
            text_id=ct.text_id,
            submission_date=ct.submission_date
        ) for ct in contest_texts
    ]


@router.delete("/{contest_id}/submissions/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_text_from_contest(
    contest_id: int,
    text_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Remove a text from a contest
    
    Can be done by:
    - The text owner
    - The contest creator
    - An admin
    """
    await ContestService.remove_text_from_contest(
        db=db,
        contest_id=contest_id,
        text_id=text_id,
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
    Assign a judge to a contest
    
    Only the contest creator or admin can assign judges
    """
    contest_judge = await ContestService.assign_judge_to_contest(
        db=db,
        contest_id=contest_id,
        assignment=assignment,
        current_user_id=current_user.id
    )
    
    return JudgeAssignmentResponse(
        contest_id=contest_judge.contest_id,
        judge_id=contest_judge.judge_id,
        assignment_date=contest_judge.assignment_date
    )


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