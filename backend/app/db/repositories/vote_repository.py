from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Vote, ContestText


class VoteRepository:
    @staticmethod
    async def create_vote(db: Session, vote_data: dict, judge_id: int, contest_id: int) -> Vote:
        """Create a new vote."""
        vote = Vote(
            judge_id=judge_id,
            contest_id=contest_id,
            **vote_data
        )
        db.add(vote)
        db.commit()
        db.refresh(vote)
        return vote

    @staticmethod
    async def get_vote(db: Session, vote_id: int) -> Optional[Vote]:
        """Get a single vote by ID."""
        return db.query(Vote).filter(Vote.id == vote_id).first()

    @staticmethod
    async def get_votes_by_contest(db: Session, contest_id: int) -> List[Vote]:
        """Get all votes for a specific contest."""
        return db.query(Vote).filter(Vote.contest_id == contest_id).all()

    @staticmethod
    async def get_votes_by_judge_and_contest(db: Session, judge_id: int, contest_id: int) -> List[Vote]:
        """Get all votes by a specific judge in a specific contest."""
        return db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id
        ).all()

    @staticmethod
    async def get_human_votes_by_judge_and_contest(db: Session, judge_id: int, contest_id: int) -> List[Vote]:
        """Get human votes by a specific judge in a specific contest."""
        return db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id,
            Vote.is_ai_vote == False
        ).all()

    @staticmethod
    async def get_ai_votes_by_judge_and_contest(db: Session, judge_id: int, contest_id: int, 
                                               ai_model: Optional[str] = None) -> List[Vote]:
        """Get AI votes by a specific judge in a specific contest, optionally filtered by AI model."""
        query = db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id,
            Vote.is_ai_vote == True
        )
        
        if ai_model:
            query = query.filter(Vote.ai_model == ai_model)
            
        return query.all()

    @staticmethod
    async def get_votes_by_text(db: Session, text_id: int) -> List[Vote]:
        """Get all votes for a specific text."""
        return db.query(Vote).filter(Vote.text_id == text_id).all()

    @staticmethod
    async def delete_vote(db: Session, vote_id: int) -> bool:
        """Delete a vote."""
        vote = db.query(Vote).filter(Vote.id == vote_id).first()
        if vote:
            db.delete(vote)
            db.commit()
            return True
        return False

    @staticmethod
    async def delete_ai_votes(db: Session, judge_id: int, contest_id: int, ai_model: str) -> int:
        """Delete all AI votes from a specific judge using a specific AI model in a contest.
        Returns the number of votes deleted."""
        votes = db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id,
            Vote.is_ai_vote == True,
            Vote.ai_model == ai_model
        ).all()
        
        count = len(votes)
        for vote in votes:
            db.delete(vote)
        
        db.commit()
        return count

    @staticmethod
    async def delete_human_votes(db: Session, judge_id: int, contest_id: int) -> int:
        """Delete all human votes from a specific judge in a contest.
        Returns the number of votes deleted."""
        votes = db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id,
            Vote.is_ai_vote == False
        ).all()
        
        count = len(votes)
        for vote in votes:
            db.delete(vote)
        
        db.commit()
        return count

    @staticmethod
    async def delete_human_vote_by_place(db: Session, judge_id: int, contest_id: int, place: int) -> bool:
        """Delete a human vote from a specific judge in a contest with a specific place.
        Returns True if a vote was deleted, False otherwise."""
        vote = db.query(Vote).filter(
            Vote.judge_id == judge_id,
            Vote.contest_id == contest_id,
            Vote.is_ai_vote == False,
            Vote.text_place == place
        ).first()
        
        if vote:
            db.delete(vote)
            db.commit()
            return True
        return False

    @staticmethod
    async def calculate_contest_results(db: Session, contest_id: int) -> None:
        """
        Calculate contest results based on votes and update the contest_texts table.
        This should be called when a contest is ready to be closed.
        Points are derived from vote.text_place (1st place = 3 points, 2nd = 2, 3rd = 1).
        """
        # Get all texts in this contest
        contest_texts_q = db.query(ContestText).filter(ContestText.contest_id == contest_id).all()
        text_ids = [ct.text_id for ct in contest_texts_q]
        
        text_total_points = {text_id: 0 for text_id in text_ids}

        all_votes_for_contest = db.query(Vote).filter(Vote.contest_id == contest_id).all()

        for vote in all_votes_for_contest:
            if vote.text_id in text_total_points:
                points_for_this_vote = 0
                if vote.text_place == 1:
                    points_for_this_vote = 3
                elif vote.text_place == 2:
                    points_for_this_vote = 2
                elif vote.text_place == 3:
                    points_for_this_vote = 1
                
                if points_for_this_vote > 0:
                    text_total_points[vote.text_id] += points_for_this_vote
        
        # Sort texts by derived points (highest first)
        # sorted_texts will be a list of tuples: (text_id, total_calculated_points)
        sorted_texts_by_points = sorted(text_total_points.items(), key=lambda item: item[1], reverse=True)
        
        # Update rankings in contest_texts
        current_rank = 0
        prev_total_points = -1 # Initialize to a value that won't match any point total
        
        processed_texts_count = 0
        rank_assignment_count = 0 # How many distinct ranks have been assigned

        for text_id, calculated_points in sorted_texts_by_points:
            ct = db.query(ContestText).filter(
                ContestText.contest_id == contest_id,
                ContestText.text_id == text_id
            ).first()
            
            if ct:
                if calculated_points != prev_total_points:
                    # New rank only if points are different from the previous text's points
                    current_rank = rank_assignment_count + 1
                    rank_assignment_count +=1
                # If points are the same as previous, they get the same current_rank
                
                ct.ranking = current_rank
                prev_total_points = calculated_points
            processed_texts_count +=1
            
        # Any texts not in sorted_texts_by_points (e.g. those with 0 points and not explicitly in text_total_points if it was pre-filtered)
        # or texts that were processed but had 0 points and didn't get a rank assigned if all ranks went to >0 point texts.
        # The current logic ensures all texts in contest_texts_q are in text_total_points, initialized to 0.
        # So, texts with 0 points will be at the end of sorted_texts_by_points.
        # If current_rank is still 0 (meaning no texts got any points), all get rank 1.
        # Otherwise, texts with 0 points get the next available rank.

        if rank_assignment_count == 0 and processed_texts_count > 0: # All texts had 0 points
             for text_id in text_ids:
                ct = db.query(ContestText).filter(ContestText.contest_id == contest_id, ContestText.text_id == text_id).first()
                if ct:
                    ct.ranking = 1
        elif processed_texts_count < len(text_ids): # Should not happen with current logic, but as a safeguard
            # This case implies some texts were not processed by the loop above, which is unlikely.
            # Assign them a rank after all others.
            unranked_ids = set(text_ids) - set(tid for tid, _ in sorted_texts_by_points)
            fallback_rank = rank_assignment_count + 1
            for text_id in unranked_ids:
                ct = db.query(ContestText).filter(ContestText.contest_id == contest_id, ContestText.text_id == text_id).first()
                if ct:
                    ct.ranking = fallback_rank
        
        db.commit() 