from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.repositories.agent_repository import AgentRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentExecuteJudge,
    AgentExecuteWriter,
    AgentExecutionResponse
)
from app.schemas.text import TextCreate
from app.schemas.vote import VoteCreate
from app.services.ai_service import AIService
from app.services.credit_service import CreditService
from app.services.text_service import TextService
from app.services.vote_service import VoteService
from app.db.repositories.user_repository import UserRepository
from app.db.models.contest_judge import ContestJudge
from app.db.models.text import Text as TextModel
from app.utils.ai_models import estimate_credits, estimate_cost_usd
from app.core.config import settings


class AgentService:
    @staticmethod
    async def create_agent(
        db: AsyncSession, agent_data: AgentCreate, owner_id: int
    ) -> Agent:
        """Create a new AI agent."""
        user_repo = UserRepository(db)
        if agent_data.is_public:
            user = await user_repo.get_by_id(owner_id)
            if not user or not user.is_admin:
                agent_data.is_public = False

        if agent_data.type not in ["judge", "writer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent type must be either 'judge' or 'writer'"
            )

        agent = await AgentRepository.create_agent(db, agent_data, owner_id)
        return agent
    
    @staticmethod
    async def get_agent_by_id(
        db: AsyncSession, agent_id: int, current_user_id: int, skip_auth_check: bool = False
    ) -> Agent:
        """Get an agent by ID if user has access to it."""
        agent = await AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        if not skip_auth_check:
            if agent.owner_id != current_user_id and not agent.is_public:
                user_repo = UserRepository(db)
                is_admin = await user_repo.is_admin(current_user_id)
                if not is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have access to this agent"
                    )
        
        return agent
    
    @staticmethod
    async def get_agents_by_owner(
        db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """Get agents belonging to a specific owner."""
        agents = await AgentRepository.get_agents_by_owner(db, owner_id, skip, limit)
        return agents
    
    @staticmethod
    async def get_public_agents(
        db: AsyncSession, agent_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """Get all public agents, optionally filtered by type."""
        if agent_type and agent_type not in ["judge", "writer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent type must be either 'judge' or 'writer'"
            )
        
        agents = await AgentRepository.get_public_agents(db, agent_type, skip, limit)
        return agents
    
    @staticmethod
    async def get_all_agents( # New method for admins
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        """Get ALL agents in the system (admin only)."""
        agents = await AgentRepository.get_all_agents_admin(db, skip, limit)
        return agents
    
    @staticmethod
    async def update_agent(
        db: AsyncSession, agent_id: int, agent_data: AgentUpdate, current_user_id: int
    ) -> Agent:
        """Update an agent if the user has permission."""
        agent = await AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        user_repo = UserRepository(db)
        is_admin = await user_repo.is_admin(current_user_id)

        if agent.owner_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this agent"
            )
        
        if agent_data.is_public is True and agent.is_public is False and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can make agents public"
            )
        
        updated_agent = await AgentRepository.update_agent(db, agent_id, agent_data)
        if not updated_agent: # Should not happen if get_agent_by_id succeeded before
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent")
        return updated_agent
    
    @staticmethod
    async def delete_agent(
        db: AsyncSession, agent_id: int, current_user_id: int
    ) -> None:
        """Delete an agent if the user has permission."""
        agent = await AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        user_repo = UserRepository(db)
        is_admin = await user_repo.is_admin(current_user_id)
        if agent.owner_id != current_user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this agent"
            )
        
        success = await AgentRepository.delete_agent(db, agent_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete agent")
        # Return None for 204
    
    @staticmethod
    async def execute_judge_agent(
        db: AsyncSession, request: AgentExecuteJudge, current_user_id: int
    ) -> List[AgentExecutionResponse]:
        """Execute a judge agent on a contest."""
        agent = await AgentService.get_agent_by_id(db, request.agent_id, current_user_id, skip_auth_check=True)
        
        if agent.type != "judge":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with id {request.agent_id} is not a judge agent"
            )
            
        user_repo = UserRepository(db)
        is_admin = await user_repo.is_admin(current_user_id)
        if agent.owner_id != current_user_id and not is_admin and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this private agent"
            )
            
        contest = await ContestRepository.get_contest(db, request.contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
            
        if contest.status != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI judging can only be performed when the contest is in evaluation state"
            )
            
        # Check if the AI agent (request.agent_id) is assigned as a judge to this contest
        ai_judge_assignment_stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == request.contest_id,
            ContestJudge.agent_judge_id == request.agent_id  # Verify the AI agent itself is assigned
        )
        ai_judge_assignment_result = await db.execute(ai_judge_assignment_stmt)
        ai_judge_is_assigned = ai_judge_assignment_result.scalar_one_or_none()

        # The rule: "Un juez, ya sea humano o IA, solo puede participar en un concurso si está registrado como juez por el creador del concurso"
        # This implies the AI agent itself must be registered.
        if not ai_judge_is_assigned:
            # Optional: Admin override? The project description implies the agent *must* be registered.
            # if not is_admin: # If we want admin to bypass this specific check
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"AI Agent with id {request.agent_id} is not assigned as a judge to this contest"
            )
            
        # The previous check for the user being a human judge is removed as it's not the primary condition.
        # The user's ability to execute this comes from owning the agent (or it being public) and having credits.
            
        texts_in_contest_models = await ContestRepository.get_contest_texts(db, contest.id)
        if not texts_in_contest_models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contest #{contest.id} has no texts to judge."
            )
            
        text_repo = TextRepository(db)
        text_details_for_ai = []
        for ct_model in texts_in_contest_models:
            text_obj = await text_repo.get_text(ct_model.text_id)
            if text_obj:
                text_details_for_ai.append({"id": text_obj.id, "title": text_obj.title, "content": text_obj.content})

        if not text_details_for_ai:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No valid text details found for judging in contest #{contest.id}.")

        # --- MODIFIED: Enhanced Pre-check Credit Estimation for Judging ---
        # Estimate input tokens using the model-aware estimator
        estimated_input_tokens, estimated_output_tokens = AgentService.estimate_judge_tokens(
            agent.prompt, 
            request.model, 
            contest.description, 
            len(text_details_for_ai)
        )
        
        estimated_cost = estimate_credits(request.model, estimated_input_tokens, estimated_output_tokens)
        # --- End of Modified Estimation ---

        if not await CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )

        execution_responses = []
        total_credits_for_run = 0

        try:
            # Call AIService.judge_contest with corrected keyword arguments
            parsed_votes_from_ai, actual_prompt_tokens, actual_completion_tokens = await AIService.judge_contest(
                model=request.model,                 # MODIFIED: was model_name
                personality_prompt=agent.prompt,     # MODIFIED: was system_prompt
                contest_description=contest.description,
                texts=text_details_for_ai
                # Temperature and max_tokens will use defaults in AIService if not passed
            )
            

            # Use estimate_credits for cost calculation based on prompt and completion tokens
            actual_credits_used = estimate_credits(request.model, actual_prompt_tokens, actual_completion_tokens)
            real_cost_usd = estimate_cost_usd(request.model, actual_prompt_tokens, actual_completion_tokens)
            actual_total_tokens_for_deduction = actual_prompt_tokens + actual_completion_tokens
            await CreditService.deduct_credits(
                    db=db,
                    user_id=current_user_id,
                    amount=actual_credits_used,
                    description=f"AI Judge Agent execution: {agent.name} on contest {request.contest_id}",
                    ai_model=request.model,
                    tokens_used=actual_total_tokens_for_deduction,
                    real_cost_usd=real_cost_usd
                )


            # Ensure contest_judge_id for the AI agent is fetched or available
            # This AI agent (request.agent_id) should be an assigned judge.
            # We need the ContestJudge.id for this AI agent in this contest to create votes.
            ai_contest_judge_entry_stmt = select(ContestJudge).filter(
                ContestJudge.contest_id == request.contest_id,
                ContestJudge.agent_judge_id == request.agent_id
            )
            ai_contest_judge_entry_result = await db.execute(ai_contest_judge_entry_stmt)
            ai_contest_judge_entry = ai_contest_judge_entry_result.scalar_one_or_none()

            if not ai_contest_judge_entry:
                # This should ideally not happen if the check at the beginning of the function passed.
                # However, it's a critical piece for vote creation.
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to find ContestJudge entry for AI agent {request.agent_id} in contest {request.contest_id} before creating votes."
                )

            # Create the agent execution record FIRST so it can be linked to votes
            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge", model=request.model, status="completed",
                credits_used=actual_credits_used
            )    
            # Delete existing AI votes for this contest_judge and model ONCE before creating new votes
            from app.db.repositories.vote_repository import VoteRepository
            deleted_count = await VoteRepository.delete_ai_votes_by_contest_judge(
                db=db,
                contest_judge_id=ai_contest_judge_entry.id,
                contest_id=request.contest_id,
                ai_model=request.model
            ) 
            print(f"DEBUG: Agent Service - Deleted {deleted_count} existing AI votes before creating new ones")

            # Now create the votes using VoteService but skipping the deletion logic
            print(f"DEBUG: Agent Service - About to create {len(parsed_votes_from_ai)} votes from AI response")
            for i, vote_info in enumerate(parsed_votes_from_ai):
                print(f"DEBUG: Agent Service - Creating vote {i+1}: text_id={vote_info.get('text_id')}, text_place={vote_info.get('text_place')}, comment='{vote_info.get('comment', 'AI Judge Auto-Comment')[:50]}...'")
                vote_create_data = VoteCreate(
                    text_id=vote_info["text_id"],
                    text_place=vote_info.get("text_place"),
                    comment=vote_info.get("comment", "AI Judge Auto-Comment"),
                    is_ai_vote=True,
                    ai_model=request.model
                )
                # Use VoteService.create_vote (deletion already handled above)
                created_vote = await VoteService.create_vote(
                    db=db,
                    vote_data=vote_create_data,
                    judge_id=request.agent_id,
                    contest_id=request.contest_id
                )
                print(f"DEBUG: Agent Service - Successfully created vote with ID {created_vote.id}, text_place={created_vote.text_place}")
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))

        except HTTPException as e:
            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge", model=request.model, status="failed",
                error_message=e.detail, credits_used=0
            )
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))
            raise e
        except Exception as e:
            error_msg = f"Error executing judge agent: {str(e)}"
            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge", model=request.model, status="failed",
                error_message=error_msg, credits_used=0
            )
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
        return execution_responses
    
    @staticmethod
    async def execute_writer_agent(
        db: AsyncSession, request: AgentExecuteWriter, current_user_id: int
    ) -> AgentExecutionResponse:
        """Execute a writer agent to generate text."""
        agent = await AgentService.get_agent_by_id(db, request.agent_id, current_user_id, skip_auth_check=True)
        
        if agent.type != "writer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with id {request.agent_id} is not a writer agent"
            )
        
        user_repo = UserRepository(db)
        is_admin = await user_repo.is_admin(current_user_id)
        if agent.owner_id != current_user_id and not is_admin and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this private agent"
            )
        
        # --- Credit Pre-check for Writer ---
        estimated_input_tokens, estimated_output_tokens = AgentService.estimate_writer_tokens(
            agent.prompt, 
            request.model, 
            request.title, 
            request.description, 
            request.contest_description
        )
        
        estimated_cost = estimate_credits(request.model, estimated_input_tokens, estimated_output_tokens)

        has_credits = await CreditService.has_sufficient_credits(db, current_user_id, estimated_cost)
        
        if not has_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )

        # Initialize variables for execution tracking
        generated_content_text: Optional[str] = None
        actual_prompt_tokens: int = 0
        actual_completion_tokens: int = 0
        actual_credits_used: int = 0
        exec_status: str = "failed"
        error_msg_for_exec: Optional[str] = None
        result_id_for_exec: Optional[int] = None
        created_text_object: Optional[TextModel] = None
        execution_record: Optional[AgentExecution] = None

        # Fetch user object to get username for author field
        user = await user_repo.get_by_id(current_user_id)
        if not user:
            # This should ideally not happen if the request was authenticated
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Executing user not found")

        try:
            generated_content_text, actual_prompt_tokens, actual_completion_tokens = await AIService.generate_text(
                model=request.model,
                personality_prompt=agent.prompt,
                user_guidance_title=request.title,
                user_guidance_description=request.description,
                contest_description=request.contest_description,
            )
            
            actual_credits_used = estimate_credits(request.model, actual_prompt_tokens, actual_completion_tokens)
            real_cost_usd = estimate_cost_usd(request.model, actual_prompt_tokens, actual_completion_tokens)
            actual_total_tokens_for_deduction = actual_prompt_tokens + actual_completion_tokens
            await CreditService.deduct_credits(
                    db=db,
                    user_id=current_user_id,
                    amount=actual_credits_used,
                    description=f"AI Writer Agent: {agent.name}",
                    ai_model=request.model,
                    tokens_used=actual_total_tokens_for_deduction,
                    real_cost_usd=real_cost_usd
                )
            exec_status = "completed"

            if generated_content_text is not None:
                # Construct author string
                author_str = f"{user.username} (via AI Agent: {agent.name} | Model: {request.model})"
                
                text_create_data = TextCreate(
                    title=request.title or f"Untitled",
                    content=generated_content_text,
                    author=author_str, # Use the constructed author string
                    # Removed author_id as TextCreate expects 'author'
                    # author_id=current_user_id, 
                    # is_ai_generated=True, # is_ai_generated is not in TextCreate schema
                    # ai_agent_id=agent.id, # ai_agent_id is not in TextCreate schema
                    # ai_model_name=request.model # ai_model_name is not in TextCreate schema
                )
                # Use TextService to create the text
                text_service = TextService(db=db)
                created_text_object = await text_service.create_text(text_data=text_create_data, current_user_id=current_user_id)
                result_id_for_exec = created_text_object.id

        except HTTPException as e:
            error_msg_for_exec = e.detail
            exec_status = "failed"
            # Re-raise to allow FastAPI to handle it
            raise e
        except Exception as e:
            error_msg_for_exec = f"An unexpected error occurred during writer agent execution: {str(e)}"
            exec_status = "failed"
            # Raise a generic 500 for unexpected errors
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg_for_exec)
        finally:
            # Always create the execution record
            execution_record = await AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="writer",
                model=request.model,
                status=exec_status,
                result_id=result_id_for_exec,
                error_message=error_msg_for_exec,
                credits_used=actual_credits_used
            )

        return AgentExecutionResponse.model_validate(execution_record)
    
    @staticmethod
    async def get_agent_executions(
        db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentExecutionResponse]:
        """Get agent executions for a user (owner of executions)."""
        executions = await AgentRepository.get_agent_executions_by_owner(db, user_id, skip, limit)
        return [AgentExecutionResponse.model_validate(exec_record) for exec_record in executions]
    
    @staticmethod
    async def clone_public_agent(
        db: AsyncSession, agent_id: int, current_user_id: int
    ) -> Agent:
        """Clone a public agent for the current user."""
        original_agent = await AgentRepository.get_agent_by_id(db, agent_id)
        
        if not original_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original agent not found"
            )
        if not original_agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot clone a private agent"
            )
        
        cloned_agent_data = AgentCreate(
            name=f"Copy of {original_agent.name}",
            description=original_agent.description,
            prompt=original_agent.prompt,
            type=original_agent.type,
            is_public=False
        )
        new_agent = await AgentRepository.create_agent(db, cloned_agent_data, current_user_id)
        return new_agent 

    @staticmethod
    def estimate_writer_tokens(
        agent_prompt: str,
        model: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        contest_description: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Estimate the number of input and output tokens for a writer agent execution.
        
        Args:
            agent_prompt: The agent's system prompt
            model: The AI model to use
            title: Optional title for the text
            description: Optional description/prompt for the text
            contest_description: Optional contest description
            
        Returns:
            Tuple of (estimated_input_tokens, estimated_output_tokens)
        """
        # Build prompt string for estimation
        prompt_str = agent_prompt
        if title: prompt_str += "\nTitle: " + title
        if description: prompt_str += "\nDescription: " + description
        if contest_description: prompt_str += "\nContest: " + contest_description
        
        # Estimate input tokens
        estimated_input_tokens = AIService.estimate_token_count(prompt_str, model_id=model)
        
        # Estimate output tokens (use default max_tokens, halved for safer estimation)
        estimated_output_tokens = settings.DEFAULT_WRITER_MAX_TOKENS // 2
        
        return estimated_input_tokens, estimated_output_tokens
    
    @staticmethod
    def estimate_judge_tokens(
        agent_prompt: str,
        model: str,
        contest_description: str,
        text_count: int,
        avg_text_length: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Estimate the number of input and output tokens for a judge agent execution.
        
        Args:
            agent_prompt: The agent's system prompt
            model: The AI model to use
            contest_description: The contest description
            text_count: Number of texts to judge
            avg_text_length: Optional average text length for more accurate estimation
            
        Returns:
            Tuple of (estimated_input_tokens, estimated_output_tokens)
        """
        # Calculate prompt tokens
        prompt_tokens_est = AIService.estimate_token_count(agent_prompt, model_id=model)
        contest_desc_tokens_est = AIService.estimate_token_count(contest_description, model_id=model)
        
        # Estimate tokens for texts
        text_tokens_est = 0
        if avg_text_length:
            text_tokens_est = text_count * avg_text_length
        else:
            # Use a default average if not provided (500 tokens per text)
            text_tokens_est = text_count * 500
        
        # Add buffer for instructions and structure
        estimated_input_tokens = prompt_tokens_est + contest_desc_tokens_est + text_tokens_est + 200
        
        # Estimate output tokens (assume ~100 tokens per evaluation + ~200 for final ranking)
        estimated_output_tokens = (text_count * 100) + 200
        
        return estimated_input_tokens, estimated_output_tokens
