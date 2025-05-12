from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationship fields
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"), nullable=False)
    contest_judge_id = Column(Integer, ForeignKey("contest_judges.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_execution_id = Column(Integer, ForeignKey("agent_executions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Vote details
    text_place = Column(Integer, nullable=True)  # 1 for first place, 2 for second, 3 for third, null for non-podium
    comment = Column(Text, nullable=False)  # Justification/feedback
    
    # Relationships
    contest = relationship("Contest")
    text = relationship("Text")
    contest_judge = relationship("ContestJudge")
    agent_execution = relationship("AgentExecution")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)