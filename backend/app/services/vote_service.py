from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.vote_repository import VoteRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.vote import VoteCreate, VoteResponse
from app.db.models import Contest, ContestJudge, User, ContestText


class VoteService:
    @staticmethod
    async def create_vote(
        db: Session, 
        vote_data: VoteCreate, 
        judge_id: int, 
        contest_id: int
    ) -> VoteResponse:
        """Create a new vote in a contest."""
        # Get the contest to check its state
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
            
        # Verify the contest is in evaluation state
        if contest.state != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Votes can only be submitted when the contest is in evaluation state"
            )
        
        # Verify the user is a judge for this contest
        judge_assignment = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        ).first()
        
        if not judge_assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned as a judge for this contest"
            )
        
        # Verify the text is part of this contest
        contest_text = db.query(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == vote_data.text_id
        ).first()
        
        if not contest_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is not part of this contest"
            )
        
        # Verify the points are valid (1, 2, or 3)
        if vote_data.points not in [1, 2, 3]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Points must be 1, 2, or 3 (third place, second place, or first place)"
            )
        
        # Check if the judge has already used this point value in this contest
        existing_votes = await VoteRepository.get_votes_by_judge_and_contest(db, judge_id, contest_id)
        
        # Check if the judge is trying to vote for the same text twice
        if any(vote.text_id == vote_data.text_id for vote in existing_votes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Judge has already voted for this text in this contest"
            )
        
        # Check if the judge is trying to assign the same points to multiple texts
        if any(vote.points == vote_data.points for vote in existing_votes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Judge has already assigned {vote_data.points} points to another text"
            )
        
        # Create the vote
        vote_dict = vote_data.dict()
        vote = await VoteRepository.create_vote(db, vote_dict, judge_id, contest_id)
        
        # Update the has_voted flag if the judge has completed all three votes
        if len(existing_votes) + 1 == 3:  # Now has 3 votes
            judge_assignment.has_voted = True
            db.commit()
            
            # Check if all judges have voted, and if so, close the contest
            await VoteService.check_contest_completion(db, contest_id)
        
        return VoteResponse.from_orm(vote)

    @staticmethod
    async def get_votes_by_contest(db: Session, contest_id: int, current_user: User) -> List[VoteResponse]:
        """Get all votes for a contest."""
        # Verify the contest exists
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Check permissions - only contest creator, judges, and admins can view votes
        is_creator = contest.creator_id == current_user.id
        is_judge = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == current_user.id
        ).first() is not None
        
        if not (is_creator or is_judge or current_user.is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view votes for this contest"
            )
        
        votes = await VoteRepository.get_votes_by_contest(db, contest_id)
        return [VoteResponse.from_orm(vote) for vote in votes]

    @staticmethod
    async def get_votes_by_judge(
        db: Session, 
        contest_id: int, 
        judge_id: int, 
        current_user: User
    ) -> List[VoteResponse]:
        """Get votes submitted by a specific judge in a contest."""
        # Verify the contest exists
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Verify the judge exists
        judge = await UserRepository.get_user_by_id(db, judge_id)
        if not judge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Judge not found"
            )
        
        # Check permissions
        is_creator = contest.creator_id == current_user.id
        is_self = judge_id == current_user.id
        
        if not (is_creator or is_self or current_user.is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these votes"
            )
        
        votes = await VoteRepository.get_votes_by_judge_and_contest(db, judge_id, contest_id)
        return [VoteResponse.from_orm(vote) for vote in votes]

    @staticmethod
    async def delete_vote(db: Session, vote_id: int, current_user: User) -> Dict[str, Any]:
        """Delete a vote."""
        vote = await VoteRepository.get_vote(db, vote_id)
        
        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )
        
        # Check permissions (only the judge who created the vote or an admin can delete it)
        if vote.judge_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this vote"
            )
        
        # Get the contest to check its state
        contest = await ContestRepository.get_contest(db, vote.contest_id)
        if contest.state == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete votes from closed contests"
            )
        
        # Update the judge's has_voted status
        judge_assignment = db.query(ContestJudge).filter(
            ContestJudge.contest_id == vote.contest_id,
            ContestJudge.judge_id == vote.judge_id
        ).first()
        
        if judge_assignment and judge_assignment.has_voted:
            judge_assignment.has_voted = False
            db.commit()
        
        success = await VoteRepository.delete_vote(db, vote_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting vote"
            )
        
        return {"message": "Vote deleted successfully"}

    @staticmethod
    async def check_contest_completion(db: Session, contest_id: int) -> None:
        """
        Check if all judges have completed their voting and close the contest if they have.
        """
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest or contest.state != "evaluation":
            return
        
        # Get all judges for this contest
        judge_assignments = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        ).all()
        
        # If there are no judges, we can't complete
        if not judge_assignments:
            return
        
        # Check if all judges have completed voting
        all_voted = all(ja.has_voted for ja in judge_assignments)
        
        # If all judges have voted, close the contest and calculate results
        if all_voted:
            # Calculate results
            await VoteRepository.calculate_contest_results(db, contest_id)
            
            # Update contest state
            contest.state = "closed"
            db.commit()
            
            # Could add notification logic here 