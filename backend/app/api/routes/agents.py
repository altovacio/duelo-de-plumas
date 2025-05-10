from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_active_user
from app.schemas.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentExecuteJudge,
    AgentExecuteWriter,
    AgentExecutionResponse
)
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new AI agent.
    Only admins can create public agents.
    """
    return await AgentService.create_agent(db, agent_data, current_user.id)


@router.get("", response_model=List[AgentResponse])
async def get_agents(
    type: Optional[str] = Query(None, description="Filter by agent type (judge or writer)"),
    public: Optional[bool] = Query(False, description="Get only public agents"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of AI agents.
    If public=True, returns public agents that anyone can use.
    Otherwise, returns agents owned by the current user.
    """
    if public:
        return await AgentService.get_public_agents(db, type, skip, limit)
    else:
        return await AgentService.get_agents_by_owner(db, current_user.id, skip, limit)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific AI agent.
    User must be the owner of the agent or the agent must be public.
    """
    return await AgentService.get_agent_by_id(db, agent_id, current_user.id)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an AI agent.
    User must be the owner of the agent to update it.
    Only admins can make agents public.
    """
    return await AgentService.update_agent(db, agent_id, agent_data, current_user.id)


@router.delete("/{agent_id}", response_model=Dict[str, bool])
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an AI agent.
    User must be the owner of the agent to delete it.
    """
    return await AgentService.delete_agent(db, agent_id, current_user.id)


@router.post("/{agent_id}/clone", response_model=AgentResponse)
async def clone_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clone a public agent to the user's account.
    The agent must be public to be cloned.
    """
    return await AgentService.clone_public_agent(db, agent_id, current_user.id)


@router.post("/execute/judge", response_model=AgentExecutionResponse)
async def execute_judge_agent(
    request: AgentExecuteJudge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a judge agent on a contest.
    - The agent must be a judge agent
    - The contest must be in evaluation state
    - User must have sufficient credits
    """
    return await AgentService.execute_judge_agent(db, request, current_user.id)


@router.post("/execute/writer", response_model=Dict)
async def execute_writer_agent(
    request: AgentExecuteWriter,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a writer agent to generate a text.
    - The agent must be a writer agent
    - User must have sufficient credits
    """
    return await AgentService.execute_writer_agent(db, request, current_user.id)


@router.get("/executions", response_model=List[AgentExecutionResponse])
async def get_agent_executions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a list of agent executions performed by the current user.
    """
    return await AgentService.get_agent_executions(db, current_user.id, skip, limit) 