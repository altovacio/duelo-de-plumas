from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
from datetime import datetime

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
    agent_execution = relationship("AgentExecution", back_populates="votes")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @property
    def judge_id(self) -> Optional[int]:
        if self.contest_judge:
            if self.contest_judge.user_judge_id:
                return self.contest_judge.user_judge_id
            elif self.contest_judge.agent_judge_id:
                 return self.contest_judge.agent_judge_id # This is agent_id for AI votes
        return None

    @property
    def is_ai_vote(self) -> bool:
        return self.agent_execution_id is not None

    @property
    def ai_model(self) -> Optional[str]:
        if self.is_ai_vote and self.agent_execution:
            return self.agent_execution.model
        return None

    @property
    def ai_version(self) -> Optional[str]:
        # "Versión base" from project description.
        # This could be the version of the agent (its prompt/mechanism) or the LLM model version.
        # Assuming Agent.version for now if it's an AI vote.
        if self.is_ai_vote and self.agent_execution and self.agent_execution.agent: # Requires AgentExecution.agent to be loaded
            return self.agent_execution.agent.version
        return None