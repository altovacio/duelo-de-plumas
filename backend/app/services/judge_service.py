from typing import List, Optional, Dict, Any, Union, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from sqlalchemy.orm import joinedload

from app.db.repositories.vote_repository import VoteRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.agent_repository import AgentRepository
from app.services.credit_service import CreditService
from app.services.ai_service import AIService
from app.schemas.vote import VoteCreate
from app.schemas.agent import AgentExecuteJudge, AgentExecutionResponse
from app.db.models import Contest, ContestJudge, User, ContestText, Vote, AgentExecution, Agent
from app.utils.ai_models import estimate_credits, estimate_cost_usd
from app.services.ai_strategies.judge_strategies import JUDGE_VERSION


class JudgeType:
    HUMAN = "human"
    AI = "ai"


class JudgeContext:
    """Context object to hold judge information regardless of type"""
    
    def __init__(self, judge_type: str, judge_id: int, user_id: int, agent_id: Optional[int] = None, 
                 model: Optional[str] = None, contest_judge_entry: Optional[ContestJudge] = None,
                 api_version: str = JUDGE_VERSION):
        self.judge_type = judge_type  # "human" or "ai"
        self.judge_id = judge_id      # user_id for human, agent_id for AI
        self.user_id = user_id        # The actual user performing the action (owner for AI agents)
        self.agent_id = agent_id      # None for human, agent_id for AI
        self.model = model            # None for human, model name for AI
        self.contest_judge_entry = contest_judge_entry
        self.api_version = api_version  # Track API version for AI strategy changes


class JudgeEstimation:
    """Container for judge execution cost estimation"""
    
    def __init__(self, estimated_credits: int, estimated_input_tokens: int, 
                 estimated_output_tokens: int, estimated_cost_usd: float):
        self.estimated_credits = estimated_credits
        self.estimated_input_tokens = estimated_input_tokens
        self.estimated_output_tokens = estimated_output_tokens
        self.estimated_cost_usd = estimated_cost_usd


class JudgeService:
    """Unified service for handling both AI and Human judge operations"""
    
    @staticmethod
    async def create_judge_votes(
        db: AsyncSession,
        contest_id: int,
        votes_data: List[VoteCreate],
        judge_context: JudgeContext,
        force_execute: bool = False
    ) -> List[Vote]:
        """
        Unified method to create votes for any judge type following the specified flow.
        """
        # Step 1: Validate contest and judge assignment
        await JudgeService._validate_contest_and_judge(db, contest_id, judge_context)
        
        # Step 2: If AI, handle AI setup
        execution_record = None
        estimation = None
        if judge_context.judge_type == JudgeType.AI:
            estimation = await JudgeService.get_judge_estimation(
                db, contest_id, judge_context.agent_id, judge_context.model
            )
            
            # Step 2.2: Check credits unless force_execute is True
            if not force_execute:
                has_credits = await CreditService.has_sufficient_credits(
                    db, judge_context.user_id, estimation.estimated_credits
                )
                if not has_credits:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Insufficient credits. Required approx: {estimation.estimated_credits}. Use force_execute=true to override."
                    )
            
            # Step 2.3: Create running execution record (no credit deduction yet)
            agent = await AgentRepository.get_agent_by_id(db, judge_context.agent_id)
            execution_record = await AgentRepository.create_agent_execution(
                db=db,
                agent_id=judge_context.agent_id,
                owner_id=judge_context.user_id,
                execution_type="judge",
                model=judge_context.model,
                status="running",
                credits_used=0,  # Will be updated in step 5
                api_version=judge_context.api_version  # Track API version
            )
        
        # Step 3: Delete previous votes from this judge for this contest
        await JudgeService._delete_previous_votes(db, contest_id, judge_context)
        
        try:
            # Step 4: Create votes
            created_votes = []
            for vote_data in votes_data:
                vote = await JudgeService._create_single_vote(
                    db, contest_id, vote_data, judge_context, execution_record
                )
                created_votes.append(vote)
            
            # Update judge completion status
            await JudgeService._update_judge_completion_status(
                db, contest_id, judge_context, created_votes
            )
            
            # Step 5: If AI, update execution record and deduct actual credits
            if execution_record and estimation:
                actual_credits_used = estimation.estimated_credits  # For now, use estimation
                execution_record.status = "completed"
                execution_record.credits_used = actual_credits_used
                
                # Deduct credits based on actual usage
                await CreditService.deduct_credits(
                    db=db,
                    user_id=judge_context.user_id,
                    amount=actual_credits_used,
                    description=f"AI Judge Agent: {agent.name}",
                    ai_model=judge_context.model,
                    tokens_used=estimation.estimated_input_tokens + estimation.estimated_output_tokens,
                    real_cost_usd=estimation.estimated_cost_usd
                )
                
                await db.commit()
            
            return created_votes
            
        except Exception as e:
            # If AI execution fails, mark execution as failed
            if execution_record:
                execution_record.status = "failed"
                execution_record.error_message = str(e)
                await db.commit()
            raise e
    
    @staticmethod
    async def get_judge_estimation(
        db: AsyncSession,
        contest_id: int,
        agent_id: int,
        model: str
    ) -> JudgeEstimation:
        """
        Get cost estimation for judge execution. 
        This method can be used by both the execution flow and frontend.
        """
        # Get agent and contest details
        agent = await AgentRepository.get_agent_by_id(db, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        contest = await ContestRepository.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        contest_texts = await ContestRepository.get_contest_texts(db, contest_id)
        
        # Calculate average text length for estimation
        if contest_texts:
            total_length = sum(len(ct.text.content) for ct in contest_texts)
            avg_text_length = total_length // len(contest_texts)
        else:
            avg_text_length = 500  # Default assumption
        
        # Estimate tokens
        estimated_input_tokens, estimated_output_tokens = JudgeService._estimate_judge_tokens(
            agent.prompt, model, contest.description, len(contest_texts), avg_text_length
        )
        
        # Calculate costs
        estimated_credits = estimate_credits(model, estimated_input_tokens, estimated_output_tokens)
        estimated_cost_usd = estimate_cost_usd(model, estimated_input_tokens, estimated_output_tokens)
        
        return JudgeEstimation(
            estimated_credits=estimated_credits,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            estimated_cost_usd=estimated_cost_usd
        )
    
    @staticmethod
    async def execute_human_vote(
        db: AsyncSession,
        contest_id: int,
        vote_data: VoteCreate,
        user_id: int
    ) -> Vote:
        """Entry point for human judge voting"""
        judge_context = await JudgeService._create_human_judge_context(db, contest_id, user_id)
        votes = await JudgeService.create_judge_votes(db, contest_id, [vote_data], judge_context)
        return votes[0]
    
    @staticmethod
    async def execute_ai_judge(
        db: AsyncSession,
        request: AgentExecuteJudge,
        user_id: int,
        force_execute: bool = False
    ) -> List[AgentExecutionResponse]:
        """Entry point for AI judge execution"""
        judge_context = await JudgeService._create_ai_judge_context(db, request, user_id)
        
        # Generate AI votes using the AI service
        votes_data = await JudgeService._generate_ai_votes(db, request, judge_context)
        
        # Create the votes using unified flow
        created_votes = await JudgeService.create_judge_votes(
            db, request.contest_id, votes_data, judge_context, force_execute
        )
        
        # Return execution response
        execution_record = await AgentRepository.get_latest_execution(
            db, judge_context.agent_id, request.model, "judge"
        )
        return [AgentExecutionResponse.model_validate(execution_record)]
    
    @staticmethod
    async def _validate_contest_and_judge(
        db: AsyncSession,
        contest_id: int,
        judge_context: JudgeContext
    ):
        """Step 1: Validate that the contest exists, is in evaluation state, and judge is assigned"""
        # Verify contest exists and is in evaluation state
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
        
        # Verify judge assignment
        if judge_context.judge_type == JudgeType.HUMAN:
            judge_stmt = select(ContestJudge).filter(
                ContestJudge.contest_id == contest_id,
                ContestJudge.user_judge_id == judge_context.judge_id
            )
        else:  # AI judge
            judge_stmt = select(ContestJudge).filter(
                ContestJudge.contest_id == contest_id,
                ContestJudge.agent_judge_id == judge_context.judge_id
            )
            
        result = await db.execute(judge_stmt)
        judge_assignment = result.scalar_one_or_none()
        
        if not judge_assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{judge_context.judge_type.title()} judge is not assigned to this contest"
            )
        
        judge_context.contest_judge_entry = judge_assignment
    
    @staticmethod
    async def _delete_previous_votes(
        db: AsyncSession,
        contest_id: int,
        judge_context: JudgeContext
    ):
        """Step 3: Delete previous votes from this judge for this contest"""
        if judge_context.judge_type == JudgeType.AI:
            # For AI judges, delete votes by contest_judge and model
            deleted_count = await VoteRepository.delete_ai_votes_by_contest_judge(
                db=db,
                contest_judge_id=judge_context.contest_judge_entry.id,
                contest_id=contest_id,
                ai_model=judge_context.model
            )
        else:
            # For human judges, delete all votes by this contest_judge
            deleted_count = await VoteRepository.delete_human_votes_by_contest_judge(
                db=db,
                contest_judge_id=judge_context.contest_judge_entry.id,
                contest_id=contest_id
            )
        
        return deleted_count
    
    @staticmethod
    async def _create_single_vote(
        db: AsyncSession,
        contest_id: int,
        vote_data: VoteCreate,
        judge_context: JudgeContext,
        execution_record: Optional[AgentExecution] = None
    ) -> Vote:
        """Step 4: Create a single vote with proper validation"""
        # Verify text exists in contest
        contest_text_stmt = select(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == vote_data.text_id
        )
        result = await db.execute(contest_text_stmt)
        contest_text = result.scalar_one_or_none()
        
        if not contest_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is not part of this contest"
            )
        
        # Validate text place if provided
        if vote_data.text_place is not None:
            total_texts_stmt = select(func.count(ContestText.id)).filter(ContestText.contest_id == contest_id)
            result = await db.execute(total_texts_stmt)
            total_texts = result.scalar_one()
            
            if vote_data.text_place not in [1, 2, 3]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text place must be 1, 2, or 3"
                )
            
            if vote_data.text_place > total_texts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot assign place {vote_data.text_place} when there are only {total_texts} texts"
                )
        
        # Prepare vote data
        vote_dict = vote_data.model_dump(exclude_unset=True)
        
        # Add execution record for AI votes
        if execution_record:
            vote_dict["agent_execution_id"] = execution_record.id
        
        # Create the vote
        return await VoteRepository.create_vote(
            db=db,
            vote_data=vote_dict,
            contest_judge_id=judge_context.contest_judge_entry.id,
            contest_id=contest_id
        )
    
    @staticmethod
    async def _update_judge_completion_status(
        db: AsyncSession,
        contest_id: int,
        judge_context: JudgeContext,
        created_votes: List[Vote]
    ):
        """Update judge completion status and check for contest completion"""
        # Count podium votes for this judge
        podium_votes_stmt = select(Vote).filter(
            Vote.contest_judge_id == judge_context.contest_judge_entry.id,
            Vote.text_place.isnot(None)
        )
        
        if judge_context.judge_type == JudgeType.HUMAN:
            podium_votes_stmt = podium_votes_stmt.filter(Vote.agent_execution_id.is_(None))
        else:
            podium_votes_stmt = podium_votes_stmt.filter(Vote.agent_execution_id.isnot(None))
        
        result = await db.execute(podium_votes_stmt)
        podium_votes = result.scalars().all()
        
        # Get total texts in contest
        total_texts_stmt = select(func.count(ContestText.id)).filter(ContestText.contest_id == contest_id)
        result = await db.execute(total_texts_stmt)
        total_texts = result.scalar_one()
        
        required_places = min(3, total_texts)
        assigned_places = len(podium_votes)
        
        # Mark judge as completed if they've assigned all required places
        if assigned_places >= required_places:
            judge_context.contest_judge_entry.has_voted = True
            await db.commit()
            
            # Check if all judges have completed voting
            await JudgeService._check_contest_completion(db, contest_id)
    
    @staticmethod
    async def _check_contest_completion(db: AsyncSession, contest_id: int):
        """Check if all judges have voted and close contest if necessary"""
        from app.services.vote_service import VoteService
        await VoteService.check_contest_completion(db, contest_id)
    
    @staticmethod
    async def _create_human_judge_context(
        db: AsyncSession,
        contest_id: int,
        user_id: int
    ) -> JudgeContext:
        """Create judge context for human judge"""
        return JudgeContext(
            judge_type=JudgeType.HUMAN,
            judge_id=user_id,
            user_id=user_id
        )
    
    @staticmethod
    async def _create_ai_judge_context(
        db: AsyncSession,
        request: AgentExecuteJudge,
        user_id: int
    ) -> JudgeContext:
        """Create judge context for AI judge"""
        # Validate agent exists and user has permission
        agent = await AgentRepository.get_agent_by_id(db, request.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        if agent.type != "judge":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent is not a judge agent"
            )
        
        # Check permissions
        user_repo = UserRepository(db)
        is_admin = await user_repo.is_admin(user_id)
        if agent.owner_id != user_id and not is_admin and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this agent"
            )
        
        return JudgeContext(
            judge_type=JudgeType.AI,
            judge_id=request.agent_id,
            user_id=user_id,
            agent_id=request.agent_id,
            model=request.model
        )
    
    @staticmethod
    async def _generate_ai_votes(
        db: AsyncSession,
        request: AgentExecuteJudge,
        judge_context: JudgeContext
    ) -> List[VoteCreate]:
        """Generate AI votes using the AI service"""
        agent = await AgentRepository.get_agent_by_id(db, judge_context.agent_id)
        contest = await ContestRepository.get_contest(db, request.contest_id)
        contest_texts = await ContestRepository.get_contest_texts(db, request.contest_id)
        
        # Generate AI response
        ai_response, actual_prompt_tokens, actual_completion_tokens = await AIService.judge_texts(
            model=request.model,
            judge_prompt=agent.prompt,
            contest_description=contest.description,
            texts_to_judge=[(ct.text.title, ct.text.content, ct.text_id) for ct in contest_texts]
        )
        
        # Parse AI response into vote data
        votes_data = []
        for vote_info in ai_response:  # Assuming ai_response is already parsed
            vote_create = VoteCreate(
                text_id=vote_info["text_id"],
                text_place=vote_info.get("text_place"),
                comment=vote_info.get("comment", "AI Judge evaluation"),
                is_ai_vote=True,
                ai_model=request.model
            )
            votes_data.append(vote_create)
        
        return votes_data
    
    @staticmethod
    def _estimate_judge_tokens(
        agent_prompt: str, 
        model: str, 
        contest_description: str,
        text_count: int, 
        avg_text_length: Optional[int] = None
    ) -> Tuple[int, int]:
        """Estimate tokens for judge execution"""
        if avg_text_length is None:
            avg_text_length = 500
        
        # Base input from prompt and contest description
        base_input = len(agent_prompt) // 4 + len(contest_description) // 4
        
        # Add estimated tokens per text (title + content + formatting)
        per_text_input = avg_text_length // 4 + 20  # Content + title + formatting
        total_input_tokens = base_input + (per_text_input * text_count)
        
        # Estimate output tokens (commentary per text + ranking)
        per_text_output = 100  # Estimated commentary per text
        ranking_output = 50    # Estimated tokens for final ranking
        total_output_tokens = (per_text_output * text_count) + ranking_output
        
        return total_input_tokens, total_output_tokens 