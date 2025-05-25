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
    async def execute_writer_agent(
        db: AsyncSession, request: AgentExecuteWriter, current_user_id: int
    ) -> AgentExecutionResponse:
        """Execute a writer agent to generate text."""
        from app.services.ai_strategies.writer_strategies import WRITER_VERSION
        
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
                # Debug parameters
                db_session=db,
                user_id=current_user_id,
                agent_id=agent.id
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
                credits_used=actual_credits_used,
                api_version=WRITER_VERSION
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
