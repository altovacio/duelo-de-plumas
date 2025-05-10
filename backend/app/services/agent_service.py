from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import re

from app.db.repositories.agent_repository import AgentRepository
from app.db.repositories.contest_repository import ContestRepository
from app.db.repositories.text_repository import TextRepository
from app.db.models.agent import Agent
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
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


class AgentService:
    @staticmethod
    async def create_agent(
        db: Session, agent_data: AgentCreate, owner_id: int
    ) -> AgentResponse:
        """Create a new AI agent."""
        # Only admins can create public agents
        if agent_data.is_public:
            user = db.query("User").filter_by(id=owner_id).first()
            if not user or not user.is_admin:
                agent_data.is_public = False  # Force private for non-admins
        
        # Validate agent type
        if agent_data.type not in ["judge", "writer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent type must be either 'judge' or 'writer'"
            )
        
        agent = AgentRepository.create_agent(db, agent_data, owner_id)
        return AgentResponse.from_orm(agent)
    
    @staticmethod
    async def get_agent_by_id(
        db: Session, agent_id: int, current_user_id: int
    ) -> AgentResponse:
        """Get an agent by ID if user has access to it."""
        agent = AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # Check if the user has access to this agent
        if agent.owner_id != current_user_id and not agent.is_public:
            # Check if the current user is an admin
            user = db.query("User").filter_by(id=current_user_id).first()
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this agent"
                )
        
        return AgentResponse.from_orm(agent)
    
    @staticmethod
    async def get_agents_by_owner(
        db: Session, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentResponse]:
        """Get agents belonging to a specific owner."""
        agents = AgentRepository.get_agents_by_owner(db, owner_id, skip, limit)
        return [AgentResponse.from_orm(agent) for agent in agents]
    
    @staticmethod
    async def get_public_agents(
        db: Session, agent_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[AgentResponse]:
        """Get all public agents, optionally filtered by type."""
        # Validate agent type if provided
        if agent_type and agent_type not in ["judge", "writer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent type must be either 'judge' or 'writer'"
            )
        
        agents = AgentRepository.get_public_agents(db, agent_type, skip, limit)
        return [AgentResponse.from_orm(agent) for agent in agents]
    
    @staticmethod
    async def update_agent(
        db: Session, agent_id: int, agent_data: AgentUpdate, current_user_id: int
    ) -> AgentResponse:
        """Update an agent if the user has permission."""
        agent = AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # Check permissions
        if agent.owner_id != current_user_id:
            # Check if the current user is an admin
            user = db.query("User").filter_by(id=current_user_id).first()
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this agent"
                )
        
        # If setting agent to public, check if user is admin
        if agent_data.is_public is True and agent.is_public is False:
            user = db.query("User").filter_by(id=current_user_id).first()
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can make agents public"
                )
        
        updated_agent = AgentRepository.update_agent(db, agent_id, agent_data)
        return AgentResponse.from_orm(updated_agent)
    
    @staticmethod
    async def delete_agent(
        db: Session, agent_id: int, current_user_id: int
    ) -> Dict[str, bool]:
        """Delete an agent if the user has permission."""
        agent = AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        # Check permissions
        if agent.owner_id != current_user_id:
            # Check if the current user is an admin
            user = db.query("User").filter_by(id=current_user_id).first()
            if not user or not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this agent"
                )
        
        success = AgentRepository.delete_agent(db, agent_id)
        return {"success": success}
    
    @staticmethod
    async def execute_judge_agent(
        db: Session, request: AgentExecuteJudge, current_user_id: int
    ) -> List[AgentExecutionResponse]:
        """Execute a judge agent on a contest."""
        agent = AgentRepository.get_agent_by_id(db, request.agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
            
        if agent.type != "judge":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with id {request.agent_id} is not a judge agent"
            )
            
        if agent.owner_id != current_user_id and not UserRepository.is_admin(db, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this agent"
            )
            
        contest = ContestRepository.get_contest_by_id(db, request.contest_id)
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
            
        judge_assignment = db.query(ContestJudge).filter(
            ContestJudge.contest_id == request.contest_id,
            ContestJudge.judge_id == current_user_id
        ).first()
        
        if not judge_assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned as a judge for this contest"
            )
            
        texts_in_contest = ContestRepository.get_texts_for_contest(db, contest.id)
        if not texts_in_contest:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contest #{contest.id} has no texts to judge."
            )
            
        text_data_for_ai = [
            {"id": text.id, "title": text.title, "content": text.content}
            for text in texts_in_contest
        ]

        estimated_input_tokens = len(agent.prompt) + len(contest.description) + sum(len(t.content) for t in texts_in_contest)
        estimated_cost = AIService.estimate_cost(request.model, estimated_input_tokens * 2)

        if not CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )
        
        execution_response_list = []

        try:
            parsed_votes_from_ai, tokens_used, cost_rate = await AIService.judge_contest(
                model=request.model,
                personality_prompt=agent.prompt,
                contest_description=contest.description,
                texts=text_data_for_ai
            )
            
            actual_cost = AIService.estimate_cost(request.model, tokens_used)
            
            CreditService.deduct_credits(
                db=db,
                user_id=current_user_id,
                amount=actual_cost,
                description=f"AI Judge: Contest #{contest.id} using {request.model}",
                ai_model=request.model,
                tokens_used=tokens_used,
                model_cost_rate=cost_rate
            )
            
            created_vote_ids = []
            if parsed_votes_from_ai:
                for vote_data_from_ai in parsed_votes_from_ai:
                    vote_create_schema = VoteCreate(
                        text_id=vote_data_from_ai["text_id"],
                        text_place=vote_data_from_ai.get("text_place"),
                        comment=vote_data_from_ai["comment"],
                        is_ai_vote=True,
                        ai_model=request.model,
                        ai_version=agent.version
                    )
                    created_vote = VoteService.create_vote(db, vote_create_schema, contest.id, current_user_id)
                    created_vote_ids.append(created_vote.id)
            
            execution_status = "completed" if parsed_votes_from_ai else "failed_to_parse_or_empty_response"
            if not parsed_votes_from_ai and tokens_used > 0:
                 execution_status = "completed_with_empty_parsed_result"
            elif not parsed_votes_from_ai and tokens_used == 0:
                 execution_status = "failed_before_llm_call_or_empty_response"

            main_execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="judge",
                model=request.model,
                status=execution_status, 
                credits_used=actual_cost,
            )
            execution_response_list.append(AgentExecutionResponse.from_orm(main_execution))

            return execution_response_list

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            failed_execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="judge",
                model=request.model,
                status="failed",
                error_message=str(e),
                credits_used=0
            )
            logger.error(f"Error executing judge agent {agent.id} for contest {contest.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing judge agent: {str(e)}"
            )
    
    @staticmethod
    async def execute_writer_agent(
        db: Session, request: AgentExecuteWriter, current_user_id: int
    ) -> Dict:
        """Execute a writer agent to generate a text."""
        agent = AgentRepository.get_agent_by_id(db, request.agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {request.agent_id} not found"
            )
        
        if agent.owner_id != current_user_id and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this agent"
            )
        
        if agent.type != "writer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with id {request.agent_id} is not a writer agent"
            )
        
        contest_description_for_ai = request.contest_description

        estimated_input_tokens = len(agent.prompt) + \
                                 (len(contest_description_for_ai) if contest_description_for_ai else 0) + \
                                 (len(request.title) if request.title else 0) + \
                                 (len(request.description) if request.description else 0)
        estimated_cost = AIService.estimate_cost(request.model, estimated_input_tokens * 3)

        if not CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required approx: {estimated_cost}"
            )

        try:
            generated_content, tokens_used, cost_rate = await AIService.generate_text(
                model=request.model,
                personality_prompt=agent.prompt,
                contest_description=contest_description_for_ai,
                user_guidance_title=request.title, 
                user_guidance_description=request.description,
            )
            
            actual_cost = AIService.estimate_cost(request.model, tokens_used)
            
            CreditService.deduct_credits(
                db=db,
                user_id=current_user_id,
                amount=actual_cost,
                description=f"AI Writer: Generation using {request.model} for agent {agent.name}",
                ai_model=request.model,
                tokens_used=tokens_used,
                model_cost_rate=cost_rate
            )
            
            # Parse title and content based on the new expected format from WRITER_BASE_PROMPT
            # Expected format:
            # Title: [The Title]
            # Text: [The Content ...]
            title_from_ai = None
            content_from_ai = generated_content # Default to full content if parsing fails

            title_match = re.search(r"^Title:\s*(.*?)$", generated_content, re.MULTILINE)
            if title_match:
                title_from_ai = title_match.group(1).strip()
                # Try to get text following the title line
                text_block_match = re.search(r"^Text:\s*(.*)", generated_content[title_match.end():].strip(), re.DOTALL | re.MULTILINE)
                if text_block_match:
                    content_from_ai = text_block_match.group(1).strip()
                else:
                    # If "Text:" not found after "Title:", assume rest of string (after title line) is content
                    # This handles cases where "Text:" might be missing but title is present
                    potential_content = generated_content[title_match.end():].strip()
                    if potential_content.lower().startswith("text:"):
                         content_from_ai = potential_content[len("text:"):].strip()
                    else:
                         content_from_ai = potential_content
            else:
                # If "Title:" prefix is not found, assume the first line is the title (old behavior as fallback)
                # and the rest is content, or the whole thing is content if no newline.
                parts = generated_content.split('\n', 1)
                title_from_ai = parts[0].strip()
                if len(parts) > 1:
                    content_from_ai = parts[1].strip()
                else:
                    # If no newline, and no "Title:" prefix, it's ambiguous.
                    # Default to no specific title, and all is content.
                    # This case should be rare if LLM follows prompt.
                    title_from_ai = None # Or keep parts[0] as title and content_from_ai as empty/same?
                    content_from_ai = parts[0].strip()

            final_title = request.title or title_from_ai or f"AI Generated Text by {agent.name}"

            text_create_data = TextCreate(
                title=final_title,
                content=content_from_ai,
                author=f"AI Agent: {agent.name} (Model: {request.model})" 
            )
            
            created_text = TextService.create_text(db=db, text_data=text_create_data, owner_id=current_user_id)
            
            execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="writer",
                model=request.model,
                status="completed",
                result_id=created_text.id,
                credits_used=actual_cost
            )
            
            return {
                "execution": AgentExecutionResponse.from_orm(execution),
                "text": created_text
            }
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            failed_execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="writer",
                model=request.model,
                status="failed",
                error_message=str(e),
                credits_used=0 
            )
            logger.error(f"Error executing writer agent {agent.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing writer agent: {str(e)}"
            )
    
    @staticmethod
    async def get_agent_executions(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentExecutionResponse]:
        """Get agent executions by a user."""
        executions = AgentRepository.get_agent_executions_by_owner(db, user_id, skip, limit)
        return [AgentExecutionResponse.from_orm(execution) for execution in executions]
    
    @staticmethod
    async def clone_public_agent(
        db: Session, agent_id: int, current_user_id: int
    ) -> AgentResponse:
        """Clone a public agent to the user's account."""
        agent = AgentRepository.get_agent_by_id(db, agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found"
            )
        
        if not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only clone public agents"
            )
        
        agent_data = AgentCreate(
            name=f"{agent.name} (Cloned)",
            description=agent.description,
            prompt=agent.prompt,
            type=agent.type,
            is_public=False  # Private by default
        )
        
        new_agent = AgentRepository.create_agent(db, agent_data, current_user_id)
        return AgentResponse.from_orm(new_agent) 