from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository:
    @staticmethod
    async def create_agent(db: AsyncSession, agent_data: AgentCreate, owner_id: int) -> Agent:
        """Create a new agent."""
        db_agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            prompt=agent_data.prompt,
            type=agent_data.type,
            is_public=agent_data.is_public,
            owner_id=owner_id
        )
        db.add(db_agent)
        await db.commit()
        await db.refresh(db_agent)
        return db_agent
    
    @staticmethod
    async def get_agent_by_id(db: AsyncSession, agent_id: int) -> Optional[Agent]:
        """Get an agent by ID."""
        stmt = select(Agent).filter(Agent.id == agent_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_agents_by_owner(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get agents belonging to a specific owner."""
        stmt = select(Agent).where(Agent.owner_id == owner_id).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_public_agents(db: AsyncSession, agent_type: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get all public agents, optionally filtered by type."""
        stmt = select(Agent).where(Agent.is_public == True)
        if agent_type:
            stmt = stmt.where(Agent.type == agent_type)
            
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def update_agent(db: AsyncSession, agent_id: int, agent_data: AgentUpdate) -> Optional[Agent]:
        """Update an agent."""
        db_agent = await AgentRepository.get_agent_by_id(db, agent_id)
        if not db_agent:
            return None
            
        update_data = agent_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_agent, key, value)
            
        await db.commit()
        await db.refresh(db_agent)
        return db_agent
    
    @staticmethod
    async def delete_agent(db: AsyncSession, agent_id: int) -> bool:
        """Delete an agent."""
        db_agent = await AgentRepository.get_agent_by_id(db, agent_id)
        if not db_agent:
            return False
            
        await db.delete(db_agent)
        await db.commit()
        return True
    
    @staticmethod
    async def get_agent_executions_by_owner(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get agent executions belonging to a specific owner."""
        stmt = select(AgentExecution).filter(
            AgentExecution.owner_id == owner_id
        ).order_by(AgentExecution.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_agent_execution_by_id(db: AsyncSession, execution_id: int) -> Optional[AgentExecution]:
        """Get an agent execution by ID."""
        stmt = select(AgentExecution).filter(AgentExecution.id == execution_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_agent_execution(
        db: AsyncSession,
        agent_id: int,
        owner_id: int,
        execution_type: str,
        model: str,
        status: str = "completed",
        result_id: Optional[int] = None,
        error_message: Optional[str] = None,
        credits_used: int = 0
    ) -> AgentExecution:
        """Create a new agent execution record."""
        db_execution = AgentExecution(
            agent_id=agent_id,
            owner_id=owner_id,
            execution_type=execution_type,
            model=model,
            status=status,
            result_id=result_id,
            error_message=error_message,
            credits_used=credits_used
        )
        db.add(db_execution)
        await db.commit()
        await db.refresh(db_execution)
        return db_execution
    
    @staticmethod
    async def get_all_agents_admin(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get all agents in the system (for admin use)."""
        stmt = select(Agent).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all() 