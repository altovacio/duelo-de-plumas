from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ContestJudge(Base):
    __tablename__ = "contest_judges"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Contest relationship defined in Contest model
    # User relationship defined in User model
    
    assignment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    has_voted = Column(Boolean, default=False)  # Tracks if judge has completed their voting duties
    
    # Create a unique constraint so a user can't be a judge for the same contest multiple times
    __table_args__ = (
        Index("contest_judge_unique", contest_id, judge_id, unique=True),
    ) 