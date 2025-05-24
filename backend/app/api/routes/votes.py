from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.schemas.vote import VoteCreate, VoteResponse
from app.services.vote_service import VoteService
from app.services.judge_service import JudgeService
from app.db.models.user import User

router = APIRouter(tags=["votes"])


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
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new vote in a contest.
    
    - The contest must be in the evaluation state
    - The user must be a judge for the contest
    - The text must be part of the contest
    
    **Voting System:**
    - Judges assign places (1st, 2nd, 3rd) to texts and provide commentary for each
    - Judges can also provide commentary for texts that didn't make the podium (no place assigned)
    
    **Human Votes:**
    - A judge must assign places to at least min(3, total_texts) different texts
    - A judge can comment on any number of texts that didn't make the podium
    - When a judge votes for the same place again, the previous vote for that place is replaced
    
    **AI Votes:**
    - Users can submit multiple votes using different AI judges (agents)
    - When voting with an AI model that was previously used, all previous votes with that model are deleted first
    - The same restrictions apply to each AI model
    - The same user can have multiple sets of votes in a contest: one as a human judge and multiple as AI judges
    
    **Small Contests:**
    - For contests with fewer than 3 texts, judges only need to assign all possible places
    - For example, in a contest with 2 texts, only 1st and 2nd places are required
    """
    # Use the new unified JudgeService for creating votes
    return await JudgeService.execute_human_vote(
        db=db,
        contest_id=contest_id,
        vote_data=vote_data,
        user_id=current_user.id
    )


@router.get(
    "/contests/{contest_id}/votes",
    response_model=List[VoteResponse],
    summary="Get all votes for a contest"
)
async def get_votes_by_contest(
    contest_id: int = Path(..., title="The ID of the contest"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all votes for a specific contest.
    
    - Only the contest creator, assigned judges, and admins can view votes for a contest
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
    vote_type: Optional[str] = Query(None, description="Filter by vote type: 'human' or 'ai'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get votes submitted by a specific judge in a contest.
    
    - Only the contest creator, the judge themselves, and admins can view a judge's votes
    - Will return all votes by the judge, including both human and AI votes
    - Use vote_type parameter to filter: 'human' for only human votes, 'ai' for only AI votes
    """
    return await VoteService.get_votes_by_judge(
        db=db,
        contest_id=contest_id,
        judge_id=judge_id,
        current_user=current_user,
        vote_type=vote_type
    )


@router.delete(
    "/votes/{vote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vote"
)
async def delete_vote(
    vote_id: int = Path(..., title="The ID of the vote to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a vote.
    
    - Only the judge who created the vote or an admin can delete it
    - Votes cannot be deleted from closed contests
    """
    await VoteService.delete_vote(
        db=db,
        vote_id=vote_id,
        current_user=current_user
    )
    return None 