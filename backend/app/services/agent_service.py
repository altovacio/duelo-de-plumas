from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.db.repositories.agent_repository import AgentRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    AgentExecuteJudge,
    AgentExecuteWriter,
    AgentExecutionResponse
)
from app.schemas.text import TextCreate, TextResponse as TextSchemaResponse
from app.schemas.vote import VoteCreate, VoteResponse as VoteSchemaResponse
from app.services.ai_service import AIService
from app.services.credit_service import CreditService
from app.services.text_service import TextService
from app.services.vote_service import VoteService
from app.db.repositories.user_repository import UserRepository
from app.db.models.contest_judge import ContestJudge
from app.db.models.user import User as UserModel
from app.db.models.text import Text as TextModel
from app.db.models.vote import Vote as VoteModel


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
            
        if contest.state != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI judging can only be performed when the contest is in evaluation state"
            )
            
        judge_assignment_stmt = select(ContestJudge).filter(
            ContestJudge.contest_id == request.contest_id,
            ContestJudge.judge_id == current_user_id
        )
        judge_assignment_result = await db.execute(judge_assignment_stmt)
        judge_assignment = judge_assignment_result.scalar_one_or_none()
        
        if not judge_assignment and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not an assigned judge for this contest or lack permissions to trigger AI judging."
            )
            
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

        estimated_input_tokens = len(agent.prompt) + len(contest.description) + sum(len(t["content"].split()) for t in text_details_for_ai)
        estimated_total_tokens = estimated_input_tokens * 2 * len(text_details_for_ai) 

        estimated_cost = await AIService.estimate_cost(request.model, estimated_total_tokens)
        if not await CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )
        
        execution_responses = []
        total_credits_for_run = 0

        try:
            parsed_votes_from_ai, actual_tokens_used, actual_cost_per_k_tokens = await AIService.judge_contest(
                model_name=request.model,
                system_prompt=agent.prompt,
                contest_description=contest.description,
                texts=text_details_for_ai
            )
            
            actual_credits_used = round((actual_tokens_used / 1000) * actual_cost_per_k_tokens)
            total_credits_for_run += actual_credits_used

            for vote_info in parsed_votes_from_ai:
                vote_create_data = VoteCreate(
                    text_id=vote_info["text_id"],
                    text_place=vote_info.get("place"),
                    comment=vote_info.get("comment", "AI Judge Auto-Comment"),
                    is_ai_vote=True,
                    ai_model=request.model
                )
                await VoteService.create_vote(db, vote_create_data, current_user_id, request.contest_id)

            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge_contest", model=request.model, status="completed",
                credits_used=actual_credits_used
            )
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))

        except HTTPException as e:
            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge_contest", model=request.model, status="failed",
                error_message=e.detail, credits_used=0
            )
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))
            raise e 
        except Exception as e:
            error_msg = f"Error executing judge agent: {str(e)}"
            exec_record = await AgentRepository.create_agent_execution(
                db=db, agent_id=agent.id, owner_id=current_user_id,
                execution_type="judge_contest", model=request.model, status="failed",
                error_message=error_msg, credits_used=0
            )
            execution_responses.append(AgentExecutionResponse.model_validate(exec_record))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
        finally:
            if total_credits_for_run > 0:
                await CreditService.deduct_credits(db, current_user_id, total_credits_for_run, f"AI Judge Agent execution: {agent.name} on contest {request.contest_id}", request.model, actual_tokens_used)

        return execution_responses
    
    @staticmethod
    async def execute_writer_agent(
        db: AsyncSession, request: AgentExecuteWriter, current_user_id: int
    ) -> TextModel:
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
        
        estimated_total_tokens = len(agent.prompt.split()) + len(request.topic.split()) * 3
        
        estimated_cost = await AIService.estimate_cost(request.model, estimated_total_tokens)
        if not await CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )
        
        generated_title = "Untitled AI Text"
        generated_content = ""
        actual_tokens_used = 0
        actual_cost_per_k_tokens = 0.0
        actual_credits_used = 0
        exec_status = "failed"
        error_msg_for_exec = None

        try:
            generated_title, generated_content, actual_tokens_used, actual_cost_per_k_tokens = await AIService.generate_text(
                model_name=request.model,
                system_prompt=agent.prompt,
                user_topic=request.topic,
                max_tokens=request.max_tokens
            )
            actual_credits_used = round((actual_tokens_used / 1000) * actual_cost_per_k_tokens)
            exec_status = "completed"

        except HTTPException as e:
            error_msg_for_exec = e.detail
            raise e
        except Exception as e:
            error_msg_for_exec = f"Error executing writer agent: {str(e)}"
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg_for_exec)
        finally:
            if actual_credits_used > 0:
                 await CreditService.deduct_credits(db, current_user_id, actual_credits_used, f"AI Writer Agent execution: {agent.name} - Topic: {request.topic[:50]}", request.model, actual_tokens_used)

        if exec_status == "completed":
            text_create_data = TextCreate(
                title=generated_title,
                content=generated_content,
                author=f"AI Agent: {agent.name} (Model: {request.model})"
            )
            text_service = TextService(db)
            created_text = await text_service.create_text(text_create_data, current_user_id)
            result_id_for_exec = created_text.id
        else:
            result_id_for_exec = None

        await AgentRepository.create_agent_execution(
            db=db, agent_id=agent.id, owner_id=current_user_id,
            execution_type="generate_text", model=request.model, status=exec_status,
            result_id=result_id_for_exec, error_message=error_msg_for_exec,
            credits_used=actual_credits_used
        )
        
        if exec_status == "completed" and created_text:
            return created_text
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg_for_exec or "AI text generation failed and no text was created.")
    
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