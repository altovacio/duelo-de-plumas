from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.orm import joinedload

from app.db.repositories.vote_repository import VoteRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.vote import VoteCreate
from app.db.models import Contest, ContestJudge, User, ContestText, Vote, AgentExecution, Agent


class VoteService:
    @staticmethod
    async def create_vote(
        db: AsyncSession, 
        vote_data: VoteCreate, 
        judge_id: int, # This is user_id for human votes, agent_id for AI votes
        contest_id: int
    ) -> Vote:
        """Create a new vote in a contest."""
        user_repo = UserRepository(db)
        # Verify the contest exists and is in the evaluation state
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
            
        if contest.status != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest is not in evaluation state"
            )
            
        # Verify the judge is assigned to this contest based on whether it's an AI vote or human vote
        if vote_data.is_ai_vote:
            judge_assignment_stmt = select(ContestJudge).filter(
                ContestJudge.contest_id == contest_id,
                ContestJudge.agent_judge_id == judge_id # Check against agent_judge_id for AI
            )
        else:
            judge_assignment_stmt = select(ContestJudge).filter(
                ContestJudge.contest_id == contest_id,
                ContestJudge.user_judge_id == judge_id # Check against user_judge_id for human
            )
            
        judge_assignment_result = await db.execute(judge_assignment_stmt)
        judge_assignment = judge_assignment_result.scalar_one_or_none()
        
        if not judge_assignment:
            judge_type = "AI agent" if vote_data.is_ai_vote else "User"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{judge_type} with id {judge_id} is not assigned as a judge to this contest"
            )
            
        # Verify the text exists in this contest
        contest_text_stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == vote_data.text_id
        )
        contest_text_result = await db.execute(contest_text_stmt)
        contest_text_obj = contest_text_result.scalar_one_or_none()
        
        if not contest_text_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is not part of this contest"
            )
            
        # Get the total number of texts in the contest to handle smaller contests
        total_texts_stmt = select(func.count(ContestText.id)).filter(ContestText.contest_id == contest_id)
        total_texts_result = await db.execute(total_texts_stmt)
        total_texts = total_texts_result.scalar_one()
        
        # Prepare data for vote creation from the input schema
        vote_dict = vote_data.model_dump(exclude_unset=True)
        
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

        # For AI votes, we need to get the latest AgentExecution for this agent and model
        if vote_data.is_ai_vote and vote_data.ai_model:
            # Find the most recent AgentExecution for this agent and model
            from app.db.repositories.agent_repository import AgentRepository
            latest_exec_stmt = select(AgentExecution).filter(
                AgentExecution.agent_id == judge_id,  # judge_id is the agent_id for AI votes
                AgentExecution.model == vote_data.ai_model,
                AgentExecution.execution_type == "judge",
                AgentExecution.status == "completed"
            ).order_by(AgentExecution.created_at.desc()).limit(1)
            
            latest_exec_result = await db.execute(latest_exec_stmt)
            latest_execution = latest_exec_result.scalar_one_or_none()
            
            if latest_execution:
                vote_dict["agent_execution_id"] = latest_execution.id
        
        # Create the vote using the prepared vote_dict
        # vote_dict contains fields from VoteCreate schema that map to Vote model columns
        vote = await VoteRepository.create_vote(
            db=db, 
            vote_data=vote_dict, # vote_dict (from VoteCreate.model_dump()) already contains text_id
            contest_judge_id=judge_assignment.id,
            contest_id=contest_id 
        )
        
        # For human votes, check if all required podium places have been assigned
        # A judge has completed their voting duties when they've assigned all possible places
        # (either all 3 places or as many as there are texts if fewer than 3)
        if not vote_data.is_ai_vote: # This implies judge_assignment.user_judge_id is not None
            podium_votes_stmt = select(Vote).filter(
                Vote.contest_judge_id == judge_assignment.id, # MODIFIED
                # Vote.contest_id == contest_id, # Redundant
                Vote.text_place.isnot(None),
                Vote.agent_execution_id.is_(None) # Ensure these are human votes
            )
            podium_votes_result = await db.execute(podium_votes_stmt)
            podium_votes = podium_votes_result.scalars().all()
            
            required_places = min(3, total_texts)
            assigned_places = len(podium_votes)
            
            if assigned_places >= required_places:
                judge_assignment.has_voted = True
                await db.commit()
                
                # Check if all judges have voted, and if so, close the contest
                await VoteService.check_contest_completion(db, contest_id)
        else:
            # For AI votes, check if the AI judge has completed voting
            # AI judge is considered complete when it has assigned all possible places
            # (either all 3 places or as many as there are texts if fewer than 3)
            ai_votes_stmt = select(Vote).filter(
                Vote.contest_judge_id == judge_assignment.id,
                Vote.text_place.isnot(None),
                Vote.agent_execution_id.isnot(None) # Ensure these are AI votes
            )
            ai_votes_result = await db.execute(ai_votes_stmt)
            ai_votes = ai_votes_result.scalars().all()
            
            required_places = min(3, total_texts)
            assigned_places = len(ai_votes)
            
            if assigned_places >= required_places:
                judge_assignment.has_voted = True
                await db.commit()
                
                # Check if all judges have voted, and if so, close the contest
                await VoteService.check_contest_completion(db, contest_id)
        
        return vote

    @staticmethod
    async def get_votes_by_contest(db: AsyncSession, contest_id: int, current_user: User) -> List[Vote]:
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
        
        # Check if current_user is any kind of judge for this contest
        # This means either their user_id is in ContestJudge.user_judge_id
        # OR they are the owner of an Agent whose agent_id is in ContestJudge.agent_judge_id
        
        # Simplified approach: check both conditions separately
        is_human_judge_stmt = select(exists().where(
            (ContestJudge.contest_id == contest_id) &
            (ContestJudge.user_judge_id == current_user.id)
        ))
        is_human_judge_result = await db.execute(is_human_judge_stmt)
        is_human_judge = is_human_judge_result.scalar_one()
        
        # Check if user owns any AI agents that are judges in this contest
        is_ai_owner_judge_stmt = select(exists().where(
            (ContestJudge.contest_id == contest_id) &
            (ContestJudge.agent_judge_id.isnot(None)) &
            (Agent.owner_id == current_user.id)
        )).select_from(
            ContestJudge.join(Agent, ContestJudge.agent_judge_id == Agent.id, isouter=False)
        )
        is_ai_owner_judge_result = await db.execute(is_ai_owner_judge_stmt)
        is_ai_owner_judge = is_ai_owner_judge_result.scalar_one()
        
        is_judge = is_human_judge or is_ai_owner_judge
        
        if not (is_creator or is_judge or current_user.is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view votes for this contest"
            )
        
        votes = await VoteRepository.get_votes_by_contest(db, contest_id)
        return votes

    @staticmethod
    async def get_votes_by_judge(
        db: AsyncSession, 
        contest_id: int, 
        judge_id: int, # This is user_id of the human judge OR owner of AI judge
        current_user: User
    ) -> List[Vote]:
        """Get votes submitted by a specific judge (user) in a contest, including their human and owned AI votes."""
        # Verify the contest exists
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Verify the judge exists
        user_repo = UserRepository(db)
        judge = await user_repo.get_by_id(judge_id)
        if not judge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Judge not found"
            )
        
        # Permissions check: Current user must be admin, or the judge themselves, or the contest creator.
        can_view = False
        if current_user.is_admin:
            can_view = True
        elif current_user.id == judge_id: # If the current user is the judge whose votes are being requested
            can_view = True
        elif contest.creator_id == current_user.id: # If current user is contest creator
            can_view = True
        
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these votes"
            )

        # Fetch ContestJudge entries related to this user (judge_id) for this contest.
        # This includes direct human judge assignments (ContestJudge.user_judge_id == judge_id)
        # AND AI agent assignments they own (ContestJudge.agent_judge.has(owner_id=judge_id)).
        contest_judge_entries_stmt = select(ContestJudge)\
            .outerjoin(Agent, ContestJudge.agent_judge_id == Agent.id)\
            .filter(
                ContestJudge.contest_id == contest_id,
                (
                    (ContestJudge.user_judge_id == judge_id) | 
                    (Agent.owner_id == judge_id) # Filter on Agent.owner_id from the joined Agent table
                )
            )
            
        contest_judge_entries_result = await db.execute(contest_judge_entries_stmt)
        contest_judge_entries = contest_judge_entries_result.scalars().all()

        if not contest_judge_entries:
            return [] # No human or owned AI judge assignments for this user in this contest

        all_votes: List[Vote] = []
        for cj_entry in contest_judge_entries:
            # Assuming VoteRepository.get_votes_by_contest_judge_id fetches all votes linked to a specific contest_judge.id
            votes = await VoteRepository.get_votes_by_contest_judge_id(db, cj_entry.id)
            all_votes.extend(votes)
            
        return all_votes

    @staticmethod
    async def delete_vote(db: AsyncSession, vote_id: int, current_user: User) -> None:
        """Delete a vote."""
        # Fetch the vote with relationships needed for permissions and logic
        # Ensure contest_judge and agent_execution (with its owner) are loaded
        stmt = select(Vote).options(
            joinedload(Vote.contest_judge).joinedload(ContestJudge.agent_judge), # Load ContestJudge and its potential Agent
            joinedload(Vote.agent_execution).joinedload(AgentExecution.owner) # Load AgentExecution and its User owner
        ).filter(Vote.id == vote_id)
        result = await db.execute(stmt)
        vote_to_delete = result.scalar_one_or_none()
        
        if not vote_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )
        
        # Check permissions
        can_delete = False
        if current_user.is_admin:
            can_delete = True
        else:
            if vote_to_delete.is_ai_vote: # Property from Vote model
                # For AI vote, current_user must be the owner of the AgentExecution
                if vote_to_delete.agent_execution and vote_to_delete.agent_execution.owner_id == current_user.id:
                    can_delete = True
            else:
                # For human vote, current_user must be the user_judge associated with the vote
                if vote_to_delete.contest_judge and vote_to_delete.contest_judge.user_judge_id == current_user.id:
                    can_delete = True
        
        if not can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this vote"
            )
        
        # Get the contest to check its state
        # contest = await ContestRepository.get_contest(db, vote_to_delete.contest_id) # Already loaded via vote_to_delete.contest if relationship is good
        # To be safe, or if contest status is critical and might change, re-fetch or ensure it's loaded.
        # For now, assuming vote_to_delete.contest relationship gives us what we need or we fetch it.
        # Let's ensure contest is loaded for status check, if not already via default relationship loading.
        contest_stmt = select(Contest).filter(Contest.id == vote_to_delete.contest_id)
        contest_res = await db.execute(contest_stmt)
        contest = contest_res.scalar_one_or_none() 

        if not contest: # Should not happen if vote exists and has valid contest_id
             raise HTTPException(status_code=500, detail="Contest not found for vote.")

        if contest.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete votes from closed contests"
            )
        
        # Update the judge's has_voted status if this is a human vote and they were marked as voted
        if not vote_to_delete.is_ai_vote: # Property from Vote model
            # contest_judge_id is directly on the vote
            if vote_to_delete.contest_judge_id:
                judge_assignment = await db.get(ContestJudge, vote_to_delete.contest_judge_id)
                if judge_assignment and judge_assignment.has_voted:
                    judge_assignment.has_voted = False
                    # No need to commit here, VoteRepository.delete_vote will commit
                    # db.add(judge_assignment) # Mark for update, commit will handle it
                    # await db.commit() # This commit is premature
            
        deleted = await VoteRepository.delete_vote(db, vote_id) # This method does its own commit
        
        # If we modified judge_assignment, ensure that change is also committed.
        # The current VoteRepository.delete_vote only deletes the vote and commits.
        # We need to commit judge_assignment changes if any.
        # Let's make this service method manage the transaction for atomicity.
        if not vote_to_delete.is_ai_vote and vote_to_delete.contest_judge_id:
            judge_assignment_for_update = await db.get(ContestJudge, vote_to_delete.contest_judge_id)
            if judge_assignment_for_update and judge_assignment_for_update.has_voted: # Check again in case of race condition (unlikely here)
                judge_assignment_for_update.has_voted = False
                db.add(judge_assignment_for_update)
        
        # The actual deletion of the vote object
        await db.delete(vote_to_delete) # Delete the vote object itself
        await db.commit() # Commit deletion and potential update to ContestJudge

        # The old call was: deleted = await VoteRepository.delete_vote(db, vote_id)
        # That repo method also did a commit. We should handle transaction here.
        # The VoteRepository.delete_vote(vote_id) fetches vote then deletes. We already have vote_to_delete.

    @staticmethod
    async def check_contest_completion(db: AsyncSession, contest_id: int) -> None:
        """
        Check if all judges have completed their voting and close the contest if they have.
        """
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest or contest.status != "evaluation":
            return
        
        # Get all judges for this contest
        assigned_judges_stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        )
        assigned_judges_result = await db.execute(assigned_judges_stmt)
        assigned_judges = assigned_judges_result.scalars().all()
        
        # If there are no judges, we can't complete
        if not assigned_judges:
            return
        
        # Check if all judges have completed voting
        all_voted = all(ja.has_voted for ja in assigned_judges)
        
        # If all judges have voted, close the contest and calculate results
        if all_voted:
            # Calculate results
            await VoteRepository.calculate_contest_results(db, contest_id)
            
            # Update contest state
            from app.schemas.contest import ContestUpdate
            contest_update = ContestUpdate(status="closed")
            await ContestRepository.update_contest(db, contest_id, contest_update)
            
            # Could add notification logic here 