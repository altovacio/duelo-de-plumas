from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository:
    @staticmethod
    def create_agent(db: Session, agent_data: AgentCreate, owner_id: int) -> Agent:
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
        db.commit()
        db.refresh(db_agent)
        return db_agent
    
    @staticmethod
    def get_agent_by_id(db: Session, agent_id: int) -> Optional[Agent]:
        """Get an agent by ID."""
        return db.query(Agent).filter(Agent.id == agent_id).first()
    
    @staticmethod
    def get_agents_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get agents belonging to a specific owner."""
        return db.query(Agent).filter(
            Agent.owner_id == owner_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_public_agents(db: Session, agent_type: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Get all public agents, optionally filtered by type."""
        query = db.query(Agent).filter(Agent.is_public == True)
        
        if agent_type:
            query = query.filter(Agent.type == agent_type)
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_agent(db: Session, agent_id: int, agent_data: AgentUpdate) -> Optional[Agent]:
        """Update an agent."""
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            return None
            
        update_data = agent_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(db_agent, key, value)
            
        db.commit()
        db.refresh(db_agent)
        return db_agent
    
    @staticmethod
    def delete_agent(db: Session, agent_id: int) -> bool:
        """Delete an agent."""
        db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not db_agent:
            return False
            
        db.delete(db_agent)
        db.commit()
        return True
    
    @staticmethod
    def get_agent_executions_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[AgentExecution]:
        """Get agent executions belonging to a specific owner."""
        return db.query(AgentExecution).filter(
            AgentExecution.owner_id == owner_id
        ).order_by(AgentExecution.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_agent_execution_by_id(db: Session, execution_id: int) -> Optional[AgentExecution]:
        """Get an agent execution by ID."""
        return db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()
    
    @staticmethod
    def create_agent_execution(
        db: Session,
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
        db.commit()
        db.refresh(db_execution)
        return db_execution 