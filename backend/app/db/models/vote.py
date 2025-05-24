from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Vote(Base):
    """
    Simplified Vote model - represents a judge's evaluation of a text in a contest.
    All complex logic moved to services/repositories to avoid async/sync conflicts.
    """
    __tablename__ = "votes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core foreign keys
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"), nullable=False)
    contest_judge_id = Column(Integer, ForeignKey("contest_judges.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Optional execution reference for AI votes
    agent_execution_id = Column(Integer, ForeignKey("agent_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Vote content
    text_place = Column(Integer, nullable=True)  # 1 for first place, 2 for second, 3 for third, null for non-podium
    comment = Column(Text, nullable=False)  # Justification/feedback
    
    # Simple flag to distinguish AI vs human votes
    is_ai = Column(Boolean, default=False, nullable=False)  # True for AI votes, False for human votes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Basic relationships (no complex logic)
    contest = relationship("Contest")
    text = relationship("Text")
    contest_judge = relationship("ContestJudge")
    agent_execution = relationship("AgentExecution", back_populates="votes")