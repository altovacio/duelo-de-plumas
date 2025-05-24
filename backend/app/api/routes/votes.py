from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.schemas.vote import VoteCreate, VoteResponse
from app.services.vote_service import VoteService
from app.services.judge_service import JudgeService
from app.db.repositories.vote_repository import VoteRepository
from app.db.models.user import User

router = APIRouter(tags=["votes"])


@router.post(
    "/contests/{contest_id}/votes",
    response_model=List[VoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit complete judging session"
)
async def create_votes(
    votes_data: List[VoteCreate],
    contest_id: int = Path(..., title="The ID of the contest"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a complete judging session with all votes for a contest.
    
    This endpoint follows the proper judging workflow:
    1. Validates contest and judge assignment once
    2. Deletes all previous votes by this judge once  
    3. Creates all new votes in one session
    4. Updates completion status once
    
    - The contest must be in the evaluation state
    - The user must be a judge for the contest
    - All texts must be part of the contest
    
    **Voting System:**
    - Judges assign places (1st, 2nd, 3rd) to texts and provide commentary for each
    - Judges can also provide commentary for texts that didn't make the podium (no place assigned)
    - A judge must assign places to at least min(3, total_texts) different texts
    
    **Features:**
    - Atomic operation (all votes succeed or all fail)
    - Efficient (one database transaction)
    - Proper credit accounting for AI judges
    """
    # Use the unified JudgeService for creating multiple votes
    votes = await JudgeService.execute_human_votes(
        db=db,
        contest_id=contest_id,
        votes_data=votes_data,
        user_id=current_user.id
    )
    
    # Convert all votes to VoteResponse
    vote_responses = []
    for vote in votes:
        vote_details = await VoteRepository.get_vote_details(db, vote.id)
        if vote_details:
            vote_response = await VoteResponse.from_vote_details(vote_details)
        else:
            # Fallback - create VoteResponse with basic info
            vote_response = VoteResponse.from_vote_model(
                vote, 
                judge_id=current_user.id, 
                is_ai_vote=False
            )
        vote_responses.append(vote_response)
    
    return vote_responses


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