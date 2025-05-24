from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete, update
from sqlalchemy.orm import selectinload

from app.db.models import Vote, ContestText, AgentExecution


class VoteRepository:
    @staticmethod
    async def create_vote(db: AsyncSession, vote_data: dict, contest_judge_id: int, contest_id: int) -> Vote:
        """Create a new vote. vote_data is expected to contain text_id."""
        # vote_data should contain text_id, comment, text_place, etc. from VoteCreate schema
        # contest_id and contest_judge_id are passed explicitly.
        # Only pass actual column fields to the Vote constructor
        allowed_keys = {"text_id", "text_place", "comment", "agent_execution_id"}
        filtered_data = {k: v for k, v in vote_data.items() if k in allowed_keys}
        vote = Vote(
            contest_judge_id=contest_judge_id,
            contest_id=contest_id,
            **filtered_data
        )
        db.add(vote)
        await db.commit()
        await db.refresh(vote)
        return vote

    @staticmethod
    async def get_vote(db: AsyncSession, vote_id: int) -> Optional[Vote]:
        """Get a single vote by ID."""
        stmt = select(Vote).filter(Vote.id == vote_id).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_votes_by_contest(db: AsyncSession, contest_id: int) -> List[Vote]:
        """Get all votes for a specific contest."""
        stmt = select(Vote).filter(Vote.contest_id == contest_id).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_votes_by_contest_judge_id(db: AsyncSession, contest_judge_id: int) -> List[Vote]:
        """Get all votes by a specific contest_judge_id."""
        stmt = select(Vote).filter(Vote.contest_judge_id == contest_judge_id).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_votes_by_text(db: AsyncSession, text_id: int) -> List[Vote]:
        """Get all votes for a specific text."""
        stmt = select(Vote).filter(Vote.text_id == text_id).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_vote(db: AsyncSession, vote_id: int) -> bool:
        """Delete a vote."""
        vote = await VoteRepository.get_vote(db, vote_id)
        if vote:
            await db.delete(vote)
            await db.commit()
            return True
        return False

    @staticmethod
    async def delete_ai_votes_by_contest_judge(db: AsyncSession, contest_judge_id: int, contest_id: int, ai_model: str) -> int:
        """Delete all AI votes associated with a specific contest_judge_id using a specific AI model.
        Returns the number of votes deleted."""
        stmt_select_ids = select(Vote.id).join(Vote.agent_execution).filter(
            Vote.contest_judge_id == contest_judge_id,
            AgentExecution.model == ai_model
        )
        vote_ids_result = await db.execute(stmt_select_ids)
        vote_ids_to_delete = vote_ids_result.scalars().all()

        if not vote_ids_to_delete:
            return 0

        stmt_delete = delete(Vote).where(Vote.id.in_(vote_ids_to_delete))
        result = await db.execute(stmt_delete)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def delete_human_vote_by_place_and_contest_judge(db: AsyncSession, contest_judge_id: int, contest_id: int, text_place: int) -> bool:
        """Delete a human vote from a specific contest_judge_id in a contest with a specific place.
        Returns True if a vote was deleted, False otherwise."""
        stmt = delete(Vote).where(
            Vote.contest_judge_id == contest_judge_id,
            Vote.agent_execution_id.is_(None),
            Vote.text_place == text_place
        ).returning(Vote.id)
        
        result = await db.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        await db.commit()
        return deleted_id is not None

    @staticmethod
    async def calculate_contest_results(db: AsyncSession, contest_id: int) -> None:
        """
        Calculate contest results based on votes and update the contest_texts table.
        This should be called when a contest is ready to be closed.
        Points are derived from vote.text_place (1st place = 3 points, 2nd = 2, 3rd = 1).
        """
        # Get all contest texts in one query to minimize database round trips
        contest_texts_stmt = select(ContestText).filter(ContestText.contest_id == contest_id)
        contest_texts_result = await db.execute(contest_texts_stmt)
        contest_texts = contest_texts_result.scalars().all()
        
        if not contest_texts:
            return  # No submissions to rank
        
        # Initialize submission data structure
        submission_data = {
            ct.text_id: {'points': 0, 'contest_text_obj': ct}
            for ct in contest_texts
        }

        # Get all votes for this contest - using direct column access to avoid lazy loading
        all_votes_stmt = select(
            Vote.text_id, 
            Vote.text_place,
            Vote.id,
            Vote.contest_judge_id,
            Vote.agent_execution_id
        ).filter(Vote.contest_id == contest_id)
        all_votes_result = await db.execute(all_votes_stmt)
        all_votes = all_votes_result.all()

        # Debug logging to understand what votes we have
        print(f"DEBUG: calculate_contest_results - Found {len(all_votes)} votes for contest {contest_id}")
        for vote_row in all_votes:
            print(f"DEBUG: Vote - text_id={vote_row.text_id}, text_place={vote_row.text_place}, vote_id={vote_row.id}, contest_judge_id={vote_row.contest_judge_id}, agent_execution_id={vote_row.agent_execution_id}")

        # Handle case with no votes: set points to 0 and ranking to None
        if not all_votes:
            for ct in contest_texts:
                ct.total_points = 0
                ct.ranking = None
            await db.commit()
            return

        # Calculate points for each text using raw column data
        for vote_row in all_votes:
            text_id = vote_row.text_id
            text_place = vote_row.text_place
            
            if text_id in submission_data and text_place is not None:
                points_to_add = 0
                if text_place == 1:
                    points_to_add = 3
                elif text_place == 2:
                    points_to_add = 2
                elif text_place == 3:
                    points_to_add = 1
                
                if points_to_add > 0:
                    submission_data[text_id]['points'] += points_to_add

        # Sort submissions by points (descending), then by submission_date (ascending) as tie-breaker
        sorted_submissions = sorted(
            submission_data.values(),
            key=lambda x: (x['points'], -x['contest_text_obj'].submission_date.timestamp()),
            reverse=True
        )

        # Assign rankings and total points
        current_rank = 0
        last_score = -1

        for i, sub_info in enumerate(sorted_submissions):
            contest_text_obj = sub_info['contest_text_obj']
            current_score = sub_info['points']

            # Update total points
            contest_text_obj.total_points = current_score

            # Assign ranking (texts with same points get same rank)
            if current_score != last_score:
                current_rank = i + 1  # Standard ranking (1, 2, 2, 4)
                last_score = current_score
            
            contest_text_obj.ranking = current_rank

        await db.commit() 