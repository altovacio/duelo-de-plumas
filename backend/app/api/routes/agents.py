from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.db.models.user import User as UserModel
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentExecuteJudge,
    AgentExecuteWriter,
    AgentExecutionResponse
)
from app.schemas.text import TextResponse as TextSchemaResponse
from app.services.agent_service import AgentService
from app.services.contest_service import ContestService
from app.services.judge_service import JudgeService
from app.utils.ai_models import estimate_credits

router = APIRouter()

class WriterCostEstimateRequest(BaseModel):
    agent_id: int
    model: str
    title: Optional[str] = None
    description: Optional[str] = None
    contest_description: Optional[str] = None

class WriterCostEstimateResponse(BaseModel):
    estimated_credits: int
    estimated_input_tokens: int
    estimated_output_tokens: int

class JudgeCostEstimateRequest(BaseModel):
    agent_id: int
    model: str
    contest_id: int

class JudgeCostEstimateResponse(BaseModel):
    estimated_credits: int
    estimated_input_tokens: int
    estimated_output_tokens: int

# First define all fixed-path routes

@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new AI agent.
    Only admins can create public agents.
    """
    return await AgentService.create_agent(db, agent_data, current_user.id)


@router.get("", response_model=List[AgentResponse])
async def get_agents(
    type: Optional[str] = Query(None, description="Filter by agent type (judge or writer)"),
    public: Optional[bool] = Query(None, description="Filter by public agents. If None, returns both public and private owned by user (or all for admin)."),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID (admin only)"),
    search: Optional[str] = Query(None, description="Search agents by name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a list of AI agents.
    - If public=True, returns only public agents.
    - If public=False, returns only private agents owned by the user (or all private for admin).
    - If public is not provided (None), returns public agents AND private agents owned by the user (or all agents for admin).
    - owner_id: Filter by specific owner (admin only)
    - search: Search in agent name and description
    """
    # Admin-only filtering by owner_id
    if owner_id is not None and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can filter by owner_id"
        )
    
    # If search is provided, use database-level search
    if search:
        # Determine public filter for search
        search_public = None
        if public is True:
            search_public = True
        elif public is False:
            search_public = False
        # If public is None, we'll search both public and private (handled in service)
        
        # For non-admin users, limit search to their own private agents + public agents
        search_owner_id = None
        if not current_user.is_admin:
            if public is False:
                # Only private agents owned by user
                search_owner_id = current_user.id
                search_public = False
            elif public is None:
                # This is complex - we need public agents + user's private agents
                # For now, we'll handle this case below with multiple queries
                pass
        else:
            # Admin can search by specific owner
            if owner_id is not None:
                search_owner_id = owner_id
        
        # Handle the complex case for non-admin users when public is None
        if not current_user.is_admin and public is None:
            # Get public agents that match search
            public_agents = await AgentService.search_agents(
                db, search, type, None, True, skip, limit
            )
            # Get user's private agents that match search  
            private_agents = await AgentService.search_agents(
                db, search, type, current_user.id, False, 0, limit
            )
            # Combine and deduplicate
            combined_agents = {agent.id: agent for agent in public_agents}
            for agent in private_agents:
                if agent.id not in combined_agents:
                    combined_agents[agent.id] = agent
            agents = list(combined_agents.values())
            # Apply manual pagination since we combined results
            agents = agents[skip:skip + limit]
        else:
            # Simple case - use database search directly
            agents = await AgentService.search_agents(
                db, search, type, search_owner_id, search_public, skip, limit
            )
        
        return agents
    
    # Original logic for non-search cases (no changes needed here)
    if public is True:
        agents = await AgentService.get_public_agents(db, type, skip, limit)
    elif public is False:
        if current_user.is_admin:
            if owner_id is not None:
                agents = await AgentService.get_agents_by_owner(db, owner_id, skip, limit)
            else:
                agents = await AgentService.get_all_agents(db, skip, limit)
                agents = [agent for agent in agents if not agent.is_public]
        else:
            agents = await AgentService.get_agents_by_owner(db, current_user.id, skip, limit)
            agents = [agent for agent in agents if not agent.is_public]
    else:
        if current_user.is_admin:
            if owner_id is not None:
                agents = await AgentService.get_agents_by_owner(db, owner_id, skip, limit)
            else:
                agents = await AgentService.get_all_agents(db, skip, limit)
        else:
            owned_agents = await AgentService.get_agents_by_owner(db, current_user.id, 0, 10000)
            public_agents = await AgentService.get_public_agents(db, type, 0, 10000)
            combined_list = {agent.id: agent for agent in owned_agents}
            for agent in public_agents:
                if agent.id not in combined_list:
                    combined_list[agent.id] = agent
            
            agents = list(combined_list.values())
            agents = agents[skip : skip + limit]
    
    # Apply type filter if provided and not already handled in database query
    if type and not search:
        agents = [agent for agent in agents if agent.type == type]
    
    return agents


@router.post("/execute/judge", response_model=List[AgentExecutionResponse])
async def execute_judge_agent(
    request: AgentExecuteJudge,
    force_execute: bool = Query(False, description="Force execution even with insufficient credits"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Execute a judge agent on a contest.
    - The agent must be a judge agent
    - The contest must be in evaluation state
    - User must have sufficient credits (unless force_execute=true)
    """
    return await JudgeService.execute_ai_judge(db, request, current_user.id, force_execute)


@router.post("/execute/writer", response_model=AgentExecutionResponse)
async def execute_writer_agent(
    request: AgentExecuteWriter,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Execute a writer agent to generate a text.
    - The agent must be a writer agent
    - User must have sufficient credits
    """
    return await AgentService.execute_writer_agent(db, request, current_user.id)


@router.get("/executions", response_model=List[AgentExecutionResponse])
async def get_agent_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a list of agent executions performed by the current user.
    """
    return await AgentService.get_agent_executions(db, current_user.id, skip=skip, limit=limit)


# Now define all parameterized routes

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get details of a specific AI agent.
    User must be the owner of the agent or the agent must be public, or user is admin.
    """
    return await AgentService.get_agent_by_id(db, agent_id, current_user.id)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update an AI agent.
    User must be the owner of the agent or admin to update it.
    Only admins can make agents public.
    """
    return await AgentService.update_agent(db, agent_id, agent_data, current_user.id)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete an AI agent.
    User must be the owner of the agent or admin to delete it.
    """
    await AgentService.delete_agent(db, agent_id, current_user.id)
    return None


@router.post("/{agent_id}/clone", response_model=AgentResponse)
async def clone_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Clone a public agent to the user's account.
    The agent must be public to be cloned.
    """
    return await AgentService.clone_public_agent(db, agent_id, current_user.id)


@router.post("/estimate/writer", response_model=WriterCostEstimateResponse)
async def estimate_writer_cost(
    request: WriterCostEstimateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Estimate the cost of executing a writer agent without actually executing it.
    """
    # Get the agent to access its prompt
    agent = await AgentService.get_agent_by_id(db, request.agent_id, current_user.id, skip_auth_check=True)
    
    if agent.type != "writer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent with id {request.agent_id} is not a writer agent"
        )
    
    # Calculate token estimates using the same method as in execution
    estimated_input_tokens, estimated_output_tokens = AgentService.estimate_writer_tokens(
        agent.prompt, 
        request.model, 
        request.title, 
        request.description, 
        request.contest_description
    )
    
    # Calculate credit estimate
    estimated_credits = estimate_credits(request.model, estimated_input_tokens, estimated_output_tokens)
    
    return WriterCostEstimateResponse(
        estimated_credits=estimated_credits,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens
    )


@router.post("/estimate/judge", response_model=JudgeCostEstimateResponse)
async def estimate_judge_cost(
    request: JudgeCostEstimateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Estimate the cost of executing a judge agent without actually executing it.
    """
    # Use the new unified estimation method
    estimation = await JudgeService.get_judge_estimation(
        db, request.contest_id, request.agent_id, request.model
    )
    
    return JudgeCostEstimateResponse(
        estimated_credits=estimation.estimated_credits,
        estimated_input_tokens=estimation.estimated_input_tokens,
        estimated_output_tokens=estimation.estimated_output_tokens
    ) 