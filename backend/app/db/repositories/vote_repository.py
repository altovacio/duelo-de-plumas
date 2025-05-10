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
    async def calculate_contest_results(db: Session, contest_id: int) -> None:
        """
        Calculate contest results based on votes and update the contest_texts table.
        This should be called when a contest is ready to be closed.
        """
        # Get all texts in this contest
        contest_texts = db.query(ContestText).filter(ContestText.contest_id == contest_id).all()
        text_ids = [ct.text_id for ct in contest_texts]
        
        # Calculate points for each text
        text_points = {}
        for text_id in text_ids:
            votes = db.query(Vote).filter(
                Vote.contest_id == contest_id,
                Vote.text_id == text_id
            ).all()
            
            points = sum(vote.points for vote in votes)
            text_points[text_id] = points
        
        # Sort texts by points (highest first)
        sorted_texts = sorted(text_points.items(), key=lambda x: x[1], reverse=True)
        
        # Update rankings in contest_texts
        current_rank = 1
        prev_points = None
        
        for text_id, points in sorted_texts:
            # Handle ties (same points get same rank)
            if prev_points is not None and points != prev_points:
                current_rank += 1
                
            ct = db.query(ContestText).filter(
                ContestText.contest_id == contest_id,
                ContestText.text_id == text_id
            ).first()
            
            if ct:
                ct.ranking = current_rank
                ct.points = points
                
            prev_points = points
        
        db.commit() 