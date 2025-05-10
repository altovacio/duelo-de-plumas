from typing import List
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.schemas.vote import VoteCreate, VoteResponse
from app.services.vote_service import VoteService
from app.db.models import User

router = APIRouter()


@router.post(
    "/contests/{contest_id}/votes",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a vote in a contest"
)
async def create_vote(
    vote_data: VoteCreate,
    contest_id: int = Path(..., title="The ID of the contest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vote in a contest.
    
    - The contest must be in the evaluation state
    - The user must be a judge for the contest
    - The text must be part of the contest
    - A judge can only assign 1st, 2nd, and 3rd place (3, 2, and 1 points respectively) once each
    """
    return await VoteService.create_vote(
        db=db,
        vote_data=vote_data,
        judge_id=current_user.id,
        contest_id=contest_id
    )


@router.get(
    "/contests/{contest_id}/votes",
    response_model=List[VoteResponse],
    summary="Get all votes for a contest"
)
async def get_votes_by_contest(
    contest_id: int = Path(..., title="The ID of the contest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all votes for a specific contest.
    
    - Only the contest creator, assigned judges, and admins can view votes
    """
    return await VoteService.get_votes_by_contest(
        db=db,
        contest_id=contest_id,
        current_user=current_user
    )


@router.get(
    "/contests/{contest_id}/votes/{judge_id}",
    response_model=List[VoteResponse],
    summary="Get votes by a specific judge in a contest"
)
async def get_votes_by_judge(
    contest_id: int = Path(..., title="The ID of the contest"),
    judge_id: int = Path(..., title="The ID of the judge"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get votes submitted by a specific judge in a contest.
    
    - Only the contest creator, the judge themselves, and admins can view a judge's votes
    """
    return await VoteService.get_votes_by_judge(
        db=db,
        contest_id=contest_id,
        judge_id=judge_id,
        current_user=current_user
    )


@router.delete(
    "/votes/{vote_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a vote"
)
async def delete_vote(
    vote_id: int = Path(..., title="The ID of the vote to delete"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a vote.
    
    - Only the judge who created the vote or an admin can delete it
    - Votes cannot be deleted from closed contests
    """
    return await VoteService.delete_vote(
        db=db,
        vote_id=vote_id,
        current_user=current_user
    ) 