from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete, update

from app.db.models import Vote, ContestText, AgentExecution


class VoteRepository:
    @staticmethod
    async def create_vote(db: AsyncSession, vote_data: dict, contest_judge_id: int, contest_id: int) -> Vote:
        """Create a new vote. vote_data is expected to contain text_id."""
        # vote_data should contain text_id, comment, text_place, etc. from VoteCreate schema
        # contest_id and contest_judge_id are passed explicitly.
        # Only pass actual column fields to the Vote constructor
        allowed_keys = {"text_id", "text_place", "comment"}
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
        stmt = select(Vote).filter(Vote.id == vote_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_votes_by_contest(db: AsyncSession, contest_id: int) -> List[Vote]:
        """Get all votes for a specific contest."""
        stmt = select(Vote).filter(Vote.contest_id == contest_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_votes_by_contest_judge_id(db: AsyncSession, contest_judge_id: int) -> List[Vote]:
        """Get all votes by a specific contest_judge_id."""
        stmt = select(Vote).filter(Vote.contest_judge_id == contest_judge_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_votes_by_text(db: AsyncSession, text_id: int) -> List[Vote]:
        """Get all votes for a specific text."""
        stmt = select(Vote).filter(Vote.text_id == text_id)
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
        # Get all texts in this contest
        contest_texts_stmt = select(ContestText).filter(ContestText.contest_id == contest_id)
        contest_texts_result = await db.execute(contest_texts_stmt)
        contest_texts_q = contest_texts_result.scalars().all()
        text_ids = [ct.text_id for ct in contest_texts_q]
        
        text_total_points = {text_id: 0 for text_id in text_ids}

        all_votes_stmt = select(Vote).filter(Vote.contest_id == contest_id)
        all_votes_result = await db.execute(all_votes_stmt)
        all_votes_for_contest = all_votes_result.scalars().all()

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
            # Fetch ContestText to update
            ct_stmt = select(ContestText).filter(
                ContestText.contest_id == contest_id,
                ContestText.text_id == text_id
            )
            ct_result = await db.execute(ct_stmt)
            ct = ct_result.scalar_one_or_none()
            
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
                ct_stmt = select(ContestText).filter(ContestText.contest_id == contest_id, ContestText.text_id == text_id)
                ct_result = await db.execute(ct_stmt)
                ct = ct_result.scalar_one_or_none()
                if ct:
                    ct.ranking = 1
        elif processed_texts_count < len(text_ids): # Should not happen with current logic, but as a safeguard
            # This case implies some texts were not processed by the loop above, which is unlikely.
            # Assign them a rank after all others.
            unranked_ids = set(text_ids) - set(tid for tid, _ in sorted_texts_by_points)
            fallback_rank = rank_assignment_count + 1
            for text_id in unranked_ids:
                ct_stmt = select(ContestText).filter(ContestText.contest_id == contest_id, ContestText.text_id == text_id)
                ct_result = await db.execute(ct_stmt)
                ct = ct_result.scalar_one_or_none()
                if ct:
                    ct.ranking = fallback_rank
        
        await db.commit() 