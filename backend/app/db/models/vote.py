from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relationship fields
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"), nullable=False)
    
    # Vote details
    points = Column(Integer, nullable=False)  # 3 for first place, 2 for second, 1 for third
    comment = Column(Text, nullable=False)  # Justification/feedback
    
    # AI metadata (if this is an AI vote)
    is_ai_vote = Column(Boolean, default=False)
    ai_model = Column(String, nullable=True)  # If is_ai_vote is True
    ai_version = Column(String, nullable=True)  # If is_ai_vote is True
    
    # Relationships
    judge = relationship("User", back_populates="votes")
    contest = relationship("Contest")
    text = relationship("Text")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Create a unique constraint that accounts for multiple vote types from same judge
    __table_args__ = (
        Index("vote_unique_with_ai", judge_id, contest_id, text_id, is_ai_vote, ai_model, unique=True),
    ) 