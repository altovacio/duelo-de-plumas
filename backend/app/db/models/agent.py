from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Agent(Base):
    """Model for AI agents (judges and writers)."""
    
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)  # Using Text for longer content
    type = Column(String, nullable=False)  # "judge" or "writer"
    is_public = Column(Boolean, default=False)
    version = Column(String, nullable=False, default="1.0")  # Version of the base mechanism
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="agents")
    # Add relationship to ContestJudge for when an agent is a judge
    contest_judges = relationship(
        "ContestJudge", 
        foreign_keys="ContestJudge.agent_judge_id", 
        back_populates="agent_judge", # Will add agent_judge to ContestJudge model
        cascade="all, delete-orphan"
    )
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan") # Assuming AgentExecution has a back_populates="agent"

# Helper for AgentType if needed, or use string directly 