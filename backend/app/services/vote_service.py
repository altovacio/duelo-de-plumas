from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.orm import joinedload, selectinload

from app.db.repositories.vote_repository import VoteRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.vote import VoteCreate, VoteResponse
from app.db.models import Contest, ContestJudge, User, Vote, Agent


class VoteService:
    @staticmethod
    async def get_votes_by_contest(db: AsyncSession, contest_id: int, current_user: User) -> List[VoteResponse]:
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
        
        # Check if current_user is a judge (either human or owns an AI agent that's a judge)
        is_judge = False
        if not is_creator and not current_user.is_admin:
            # Check if user is a human judge
            human_judge_stmt = select(exists().where(
                (ContestJudge.contest_id == contest_id) &
                (ContestJudge.user_judge_id == current_user.id)
            ))
            human_judge_result = await db.execute(human_judge_stmt)
            is_human_judge = human_judge_result.scalar_one()
            
            # Check if user owns any AI agents that are judges
            ai_judge_stmt = select(exists().where(
                (ContestJudge.contest_id == contest_id) &
                (ContestJudge.agent_judge_id.isnot(None)) &
                (Agent.owner_id == current_user.id)
            )).select_from(
                ContestJudge.join(Agent, ContestJudge.agent_judge_id == Agent.id)
            )
            ai_judge_result = await db.execute(ai_judge_stmt)
            is_ai_judge = ai_judge_result.scalar_one()
            
            is_judge = is_human_judge or is_ai_judge
        
        if not (is_creator or is_judge or current_user.is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view votes for this contest"
            )
        
        # Get all votes for this contest with relationships loaded
        votes_stmt = select(Vote).filter(Vote.contest_id == contest_id).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        votes_result = await db.execute(votes_stmt)
        votes = votes_result.scalars().all()
        
        # Convert to VoteResponse using the simplified approach
        vote_responses = []
        for vote in votes:
            # For VoteResponse, we need to determine the judge_id and AI details
            judge_id_for_response = None
            ai_model = None
            ai_version = None
            
            if vote.is_ai:
                # For AI votes, judge_id is the agent_id
                if vote.contest_judge and vote.contest_judge.agent_judge_id:
                    judge_id_for_response = vote.contest_judge.agent_judge_id
                
                # Get AI model and version from agent_execution
                if vote.agent_execution:
                    ai_model = vote.agent_execution.model
                    # Get AI version - we need to fetch the agent
                    if vote.agent_execution.agent_id:
                        agent_stmt = select(Agent.version).filter(Agent.id == vote.agent_execution.agent_id)
                        agent_result = await db.execute(agent_stmt)
                        ai_version = agent_result.scalar_one_or_none()
            else:
                # For human votes, judge_id is the user_judge_id
                if vote.contest_judge and vote.contest_judge.user_judge_id:
                    judge_id_for_response = vote.contest_judge.user_judge_id
            
            vote_response = VoteResponse.from_vote_model(
                vote=vote,
                judge_id=judge_id_for_response,
                is_ai_vote=vote.is_ai,
                ai_model=ai_model,
                ai_version=ai_version
            )
            vote_responses.append(vote_response)
        
        return vote_responses

    @staticmethod
    async def get_votes_by_judge(
        db: AsyncSession, 
        contest_id: int, 
        judge_id: int,  # This is user_id who we want to see votes for
        current_user: User,
        vote_type: Optional[str] = None  # 'human', 'ai', or None for all
    ) -> List[VoteResponse]:
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
        
        # Permissions check: Current user must be admin, or the judge themselves, or the contest creator
        can_view = (
            current_user.is_admin or 
            current_user.id == judge_id or 
            contest.creator_id == current_user.id
        )
        
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these votes"
            )

        # Validate vote_type parameter
        if vote_type and vote_type not in ['human', 'ai']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="vote_type must be 'human' or 'ai'"
            )

        # Get all contest judge assignments for this user (both human and AI agents they own)
        contest_judges_stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        )
        
        # Add filter for human judge assignments
        if vote_type == 'human':
            contest_judges_stmt = contest_judges_stmt.filter(
                ContestJudge.user_judge_id == judge_id
            )
        elif vote_type == 'ai':
            # For AI, we need to join with agents to check ownership
            contest_judges_stmt = contest_judges_stmt.join(
                Agent, ContestJudge.agent_judge_id == Agent.id
            ).filter(Agent.owner_id == judge_id)
        else:
            # For all types, get both human assignments and AI agent assignments they own
            contest_judges_stmt = contest_judges_stmt.outerjoin(
                Agent, ContestJudge.agent_judge_id == Agent.id
            ).filter(
                (ContestJudge.user_judge_id == judge_id) | 
                (Agent.owner_id == judge_id)
            )
            
        contest_judges_result = await db.execute(contest_judges_stmt)
        contest_judges = contest_judges_result.scalars().all()

        if not contest_judges:
            return []  # No judge assignments for this user in this contest

        # Get all contest_judge_ids
        contest_judge_ids = [cj.id for cj in contest_judges]
        
        # Now get votes for these contest judges, filtering by vote_type if specified
        votes_stmt = select(Vote).filter(
            Vote.contest_judge_id.in_(contest_judge_ids)
        ).options(
            selectinload(Vote.contest_judge),
            selectinload(Vote.agent_execution)
        )
        
        # Apply vote_type filter using the is_ai column
        if vote_type == 'human':
            votes_stmt = votes_stmt.filter(Vote.is_ai == False)
        elif vote_type == 'ai':
            votes_stmt = votes_stmt.filter(Vote.is_ai == True)
        
        votes_result = await db.execute(votes_stmt)
        votes = votes_result.scalars().all()
        
        # Convert to VoteResponse using the simplified approach
        vote_responses = []
        for vote in votes:
            # For VoteResponse, we need to determine the judge_id and AI details
            judge_id_for_response = None
            ai_model = None
            ai_version = None
            
            if vote.is_ai:
                # For AI votes, judge_id is the agent_id
                if vote.contest_judge and vote.contest_judge.agent_judge_id:
                    judge_id_for_response = vote.contest_judge.agent_judge_id
                
                # Get AI model and version from agent_execution
                if vote.agent_execution:
                    ai_model = vote.agent_execution.model
                    # Get AI version - we need to fetch the agent
                    if vote.agent_execution.agent_id:
                        agent_stmt = select(Agent.version).filter(Agent.id == vote.agent_execution.agent_id)
                        agent_result = await db.execute(agent_stmt)
                        ai_version = agent_result.scalar_one_or_none()
            else:
                # For human votes, judge_id is the user_judge_id
                if vote.contest_judge and vote.contest_judge.user_judge_id:
                    judge_id_for_response = vote.contest_judge.user_judge_id
            
            vote_response = VoteResponse.from_vote_model(
                vote=vote,
                judge_id=judge_id_for_response,
                is_ai_vote=vote.is_ai,
                ai_model=ai_model,
                ai_version=ai_version
            )
            vote_responses.append(vote_response)
        
        return vote_responses

    @staticmethod
    async def delete_vote(db: AsyncSession, vote_id: int, current_user: User) -> None:
        """Delete a vote."""
        # Fetch the vote with relationships needed for permissions and logic
        stmt = select(Vote).options(
            joinedload(Vote.contest_judge).joinedload(ContestJudge.agent_judge),
            joinedload(Vote.agent_execution).joinedload(AgentExecution.owner)
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
            if vote_to_delete.is_ai:
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
        contest_stmt = select(Contest).filter(Contest.id == vote_to_delete.contest_id)
        contest_res = await db.execute(contest_stmt)
        contest = contest_res.scalar_one_or_none() 

        if not contest:
             raise HTTPException(status_code=500, detail="Contest not found for vote.")

        if contest.status == "closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete votes from closed contests"
            )
        
        # Update the judge's has_voted status if this is a human vote and they were marked as voted
        if not vote_to_delete.is_ai:
            # Check if removing this vote means the judge hasn't completed voting anymore
            total_texts_stmt = select(func.count(ContestText.id)).filter(ContestText.contest_id == vote_to_delete.contest_id)
            total_texts_result = await db.execute(total_texts_stmt)
            total_texts = total_texts_result.scalar_one()
            
            # Get remaining human votes after deletion
            remaining_votes_stmt = select(Vote).filter(
                Vote.contest_judge_id == vote_to_delete.contest_judge_id,
                Vote.text_place.isnot(None),
                Vote.is_ai == False,
                Vote.id != vote_id  # Exclude the vote being deleted
            )
            remaining_votes_result = await db.execute(remaining_votes_stmt)
            remaining_votes = remaining_votes_result.scalars().all()
            
            required_places = min(3, total_texts)
            if len(remaining_votes) < required_places and vote_to_delete.contest_judge:
                vote_to_delete.contest_judge.has_voted = False
                await db.commit()
        
        # Delete the vote
        await db.delete(vote_to_delete)
        await db.commit()

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