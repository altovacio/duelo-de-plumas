from typing import List, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
        # Verify the agent exists and is a judge agent
        agent = await AgentRepository.get_agent(db, request.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
            
        if agent.type != "judge":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This operation requires a judge agent"
            )
            
        # Verify the user owns the agent or is an admin
        if agent.owner_id != current_user_id and not UserRepository.is_admin(db, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to use this agent"
            )
            
        # Verify the contest exists
        contest = await ContestRepository.get_contest(db, request.contest_id)
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
            
        # Verify the contest is in evaluation state
        if contest.state != "evaluation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI judging can only be performed when the contest is in evaluation state"
            )
            
        # Verify the user is a judge for this contest
        judge_assignment = db.query(ContestJudge).filter(
            ContestJudge.contest_id == request.contest_id,
            ContestJudge.judge_id == current_user_id
        ).first()
        
        if not judge_assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned as a judge for this contest"
            )
            
        # Get all texts in the contest
        texts = await ContestRepository.get_contest_texts(db, request.contest_id)
        if not texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No texts found in this contest"
            )
            
        # Prepare text data for AI service
        text_data = []
        for ct in texts:
            text_data.append({
                "id": ct.text.id,
                "title": ct.text.title,
                "content": ct.text.content
            })
            
        # Check if we have enough texts for a proper ranking (need at least 3)
        if len(text_data) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest must have at least 3 texts for AI judging"
            )
            
        # Estimate token usage for this operation
        estimated_tokens = AIService.estimate_tokens_for_judging(
            model=request.model,
            prompt_length=len(agent.prompt),
            contest_desc_length=len(contest.description),
            texts=text_data
        )
        
        # Estimate cost based on tokens
        estimated_cost = AIService.estimate_cost(request.model, estimated_tokens)
        
        # Check if user has enough credits
        user = await UserRepository.get_user_by_id(db, current_user_id)
        if user.credits < estimated_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. This operation requires approximately {estimated_cost} credits."
            )
            
        try:
            # Call AI service to judge contest texts
            judge_results, tokens_used, cost_rate = await AIService.judge_contest(
                model=request.model,
                judge_prompt=agent.prompt,
                contest_description=contest.description,
                texts=text_data
            )
            
            # Calculate actual cost based on tokens used
            actual_cost = AIService.estimate_cost(request.model, tokens_used)
            
            # Deduct credits
            CreditService.deduct_credits(
                db=db,
                user_id=current_user_id,
                amount=actual_cost,
                description=f"AI Judge: Contest #{contest.id} using {request.model}",
                ai_model=request.model,
                tokens_used=tokens_used,
                model_cost_rate=cost_rate
            )
            
            # Create an agent execution record
            execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="judge",
                model=request.model,
                status="completed",
                credits_used=actual_cost
            )
            
            # Submit votes for the contest - no need to delete previous votes
            # as the vote_service will handle deleting previous AI votes with the same model
            for result in judge_results:
                vote_data = VoteCreate(
                    text_id=result["text_id"],
                    points=result["points"],
                    comment=result["comment"],
                    is_ai_vote=True,
                    ai_model=request.model,
                    ai_version=agent.version
                )
                # Submit vote
                await VoteService.create_vote(
                    db=db, 
                    contest_id=contest.id, 
                    vote_data=vote_data, 
                    judge_id=current_user_id  # AI votes are owned by the user who ran the agent
                )
            
            return AgentExecutionResponse.from_orm(execution)
            
        except Exception as e:
            # Log the error
            print(f"Error in AI judging: {str(e)}")
            
            # Create a failed execution record
            execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="judge",
                model=request.model,
                status="failed",
                error_message=str(e),
                credits_used=0  # No credits used if failed
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI judging failed: {str(e)}"
            )
    
    @staticmethod
    async def execute_writer_agent(
        db: Session, request: AgentExecuteWriter, current_user_id: int
    ) -> Dict:
        """Execute a writer agent to generate a text."""
        # Get agent and check permissions
        agent = AgentRepository.get_agent_by_id(db, request.agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {request.agent_id} not found"
            )
        
        # Check if agent is public or owned by user
        if agent.owner_id != current_user_id and not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this agent"
            )
        
        # Check if agent is a writer
        if agent.type != "writer":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with id {request.agent_id} is not a writer agent"
            )
        
        # Build prompt
        prompt = agent.prompt
        
        if request.title:
            prompt += f"\n\nTitle: {request.title}"
        
        if request.description:
            prompt += f"\n\nDescription: {request.description}"
        
        # Estimate the cost of this operation
        estimated_cost = AIService.estimate_cost(request.model, len(prompt) * 2)  # Rough estimate
        
        # Check if user has enough credits
        if not CreditService.has_sufficient_credits(db, current_user_id, estimated_cost):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required: {estimated_cost}"
            )
        
        try:
            # Call AI service to generate text
            generated_text, tokens_used, cost_rate = await AIService.generate_text(
                model=request.model,
                prompt=prompt,
                system_message="You are a creative writer. Write an original text based on the given instructions and personality."
            )
            
            # Calculate actual cost based on tokens used
            actual_cost = AIService.estimate_cost(request.model, tokens_used)
            
            # Deduct credits
            CreditService.deduct_credits(
                db=db,
                user_id=current_user_id,
                amount=actual_cost,
                description=f"AI Writer: Generation using {request.model}",
                ai_model=request.model,
                tokens_used=tokens_used,
                model_cost_rate=cost_rate
            )
            
            # Create the text
            text_data = TextCreate(
                title=request.title or f"AI Generated Text by {agent.name}",
                content=generated_text,
                author=f"AI Agent: {agent.name}" 
            )
            
            created_text = TextService.create_text(db, text_data, current_user_id)
            
            # Create an agent execution record
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
            
        except Exception as e:
            # Record failed execution
            execution = AgentRepository.create_agent_execution(
                db=db,
                agent_id=agent.id,
                owner_id=current_user_id,
                execution_type="writer",
                model=request.model,
                status="failed",
                error_message=str(e),
                credits_used=0  # No credits used for failed execution
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute writer agent: {str(e)}"
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
        
        # Check if agent is public
        if not agent.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only clone public agents"
            )
        
        # Create a new agent based on the public one
        agent_data = AgentCreate(
            name=f"{agent.name} (Cloned)",
            description=agent.description,
            prompt=agent.prompt,
            type=agent.type,
            is_public=False  # Private by default
        )
        
        new_agent = AgentRepository.create_agent(db, agent_data, current_user_id)
        return AgentResponse.from_orm(new_agent) 