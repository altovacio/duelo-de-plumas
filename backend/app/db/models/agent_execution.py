from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class AgentExecution(Base):
    """Model for tracking AI agent executions."""
    
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    execution_type = Column(String, nullable=False)  # "judge" or "writer"
    model = Column(String, nullable=False)  # LLM model used
    status = Column(String, nullable=False)  # "completed" or "failed"
    result_id = Column(Integer, nullable=True)  # ID of the resulting text or votes
    error_message = Column(String, nullable=True)  # If status is "failed"
    credits_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User")
    agent = relationship("Agent", lazy="joined")
    votes = relationship("Vote", back_populates="agent_execution") 