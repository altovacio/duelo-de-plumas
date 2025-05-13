from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(tags=["agents"])


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
    """
    if public is True:
        return await AgentService.get_public_agents(db, type, skip, limit)
    elif public is False:
        if current_user.is_admin:
            all_agents = await AgentService.get_all_agents(db, skip, limit)
            return [agent for agent in all_agents if not agent.is_public]
        else:
            owned_agents = await AgentService.get_agents_by_owner(db, current_user.id, skip, limit)
            return [agent for agent in owned_agents if not agent.is_public]
    else:
        if current_user.is_admin:
            return await AgentService.get_all_agents(db, skip, limit)
        else:
            owned_agents = await AgentService.get_agents_by_owner(db, current_user.id, 0, 10000)
            public_agents = await AgentService.get_public_agents(db, type, 0, 10000)
            combined_list = {agent.id: agent for agent in owned_agents}
            for agent in public_agents:
                if agent.id not in combined_list:
                    combined_list[agent.id] = agent
            
            all_relevant_agents = list(combined_list.values())
            return all_relevant_agents[skip : skip + limit]


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


@router.post("/execute/judge", response_model=List[AgentExecutionResponse])
async def execute_judge_agent(
    request: AgentExecuteJudge,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Execute a judge agent on a contest.
    - The agent must be a judge agent
    - The contest must be in evaluation state
    - User must have sufficient credits
    """
    return await AgentService.execute_judge_agent(db, request, current_user.id)


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