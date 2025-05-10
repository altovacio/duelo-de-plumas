from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.vote_repository import VoteRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.vote import VoteCreate, VoteResponse
from app.db.models import Contest, ContestJudge, User, ContestText, Vote


class VoteService:
    @staticmethod
    async def create_vote(
        db: Session, 
        vote_data: VoteCreate, 
        judge_id: int, 
        contest_id: int
    ) -> VoteResponse:
        """Create a new vote in a contest."""
        # Verify the contest exists and is in the evaluation state
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
            
        if contest.state != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest is not in evaluation state"
            )
            
        # Verify the judge is assigned to this contest
        judge_assignment = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        ).first()
        
        if not judge_assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned as a judge to this contest"
            )
            
        # Verify the text exists in this contest
        contest_text = db.query(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == vote_data.text_id
        ).first()
        
        if not contest_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is not part of this contest"
            )
            
        # Get the total number of texts in the contest to handle smaller contests
        total_texts = db.query(ContestText).filter(
            ContestText.contest_id == contest_id
        ).count()
        
        # Prepare data for vote creation from the input schema
        vote_dict = vote_data.dict()
        
        # If text_place is provided, validate it
        if vote_data.text_place is not None:
            # Validate text_place (must be 1, 2, or 3)
            if vote_data.text_place not in [1, 2, 3]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text place must be 1, 2, or 3 (first, second, or third place)"
                )
                
            # Ensure we don't assign places beyond the number of texts
            if vote_data.text_place > total_texts:
                detail_msg = (
                    f"Cannot assign place {vote_data.text_place} "
                    f"when there are only {total_texts} texts"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail_msg
                )

        
        # Handle differently based on whether this is a human or AI vote
        if vote_data.is_ai_vote:
            # For AI votes, we first delete any existing votes from this judge with the same AI model
            if not vote_data.ai_model:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="AI votes must specify the AI model used"
                )
                
            # Delete existing AI votes with this model
            await VoteRepository.delete_ai_votes(db, judge_id, contest_id, vote_data.ai_model)
            
            # Get current AI votes for this model after deletion
            existing_votes = await VoteRepository.get_ai_votes_by_judge_and_contest(
                db, judge_id, contest_id, vote_data.ai_model
            )
            
            # Check if the AI is trying to vote for the same text twice (shouldn't happen after deletion)
            if any(v.text_id == vote_data.text_id for v in existing_votes):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="AI has already voted for this text in this contest with the same model"
                )
            
            # If assigning a place, check if already assigned
            if vote_data.text_place is not None:
                if any(v.text_place == vote_data.text_place for v in existing_votes if v.text_place is not None):
                    detail_msg = (
                        f"AI has already assigned place {vote_data.text_place} "
                        f"to another text in this contest"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=detail_msg
                    )
        else:
            # For human votes, we handle separately:
            # 1. If it's a podium vote (1st, 2nd, 3rd), delete any previous vote with the same place
            # 2. For non-podium votes, just check if we already commented on this text
            
            if vote_data.text_place is not None:
                # Delete any previous vote with the same place
                await VoteRepository.delete_human_vote_by_place(db, judge_id, contest_id, vote_data.text_place)
            else:
                # For non-podium votes, check if we already commented on this text
                existing_vote = db.query(Vote).filter(
                    Vote.judge_id == judge_id,
                    Vote.contest_id == contest_id,
                    Vote.text_id == vote_data.text_id,
                    Vote.is_ai_vote == False
                ).first()
                
                if existing_vote:
                    # If the vote exists, update it instead of creating a new one
                    existing_vote.comment = vote_data.comment
                    existing_vote.text_place = vote_data.text_place # If we allow updating place for non-podium to podium
                    db.commit()
                    db.refresh(existing_vote)
                    return VoteResponse.from_orm(existing_vote)
        
        # Create the vote using the prepared vote_dict
        # vote_dict contains fields from VoteCreate schema that map to Vote model columns
        vote = await VoteRepository.create_vote(db, vote_dict, judge_id, contest_id)
        
        # For human votes, check if all required podium places have been assigned
        # A judge has completed their voting duties when they've assigned all possible places
        # (either all 3 places or as many as there are texts if fewer than 3)
        if not vote_data.is_ai_vote:
            podium_votes = db.query(Vote).filter(
                Vote.judge_id == judge_id,
                Vote.contest_id == contest_id,
                Vote.is_ai_vote == False,
                Vote.text_place.isnot(None)
            ).all()
            
            required_places = min(3, total_texts)
            assigned_places = len(podium_votes)
            
            if assigned_places >= required_places:
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
                detail="You don\'t have permission to view votes for this contest"
            )
        
        votes = await VoteRepository.get_votes_by_contest(db, contest_id)
        return [VoteResponse.from_orm(v) for v in votes]

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
                detail="You don\'t have permission to view these votes"
            )
        
        votes = await VoteRepository.get_votes_by_judge_and_contest(db, judge_id, contest_id)
        return [VoteResponse.from_orm(v) for v in votes]

    @staticmethod
    async def delete_vote(db: Session, vote_id: int, current_user: User) -> Dict[str, Any]:
        """Delete a vote."""
        vote_to_delete = await VoteRepository.get_vote(db, vote_id) # Renamed variable
        
        if not vote_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )
        
        # Check permissions (only the judge who created the vote or an admin can delete it)
        if vote_to_delete.judge_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don\'t have permission to delete this vote"
            )
        
        # Get the contest to check its state
        contest = await ContestRepository.get_contest(db, vote_to_delete.contest_id)
        if contest.state == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete votes from closed contests"
            )
        
        # Update the judge's has_voted status if this is a human vote
        if not vote_to_delete.is_ai_vote:
            judge_assignment = db.query(ContestJudge).filter(
                ContestJudge.contest_id == vote_to_delete.contest_id,
                ContestJudge.judge_id == vote_to_delete.judge_id
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