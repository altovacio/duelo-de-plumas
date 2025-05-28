from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ContestMember(Base):
    __tablename__ = "contest_members"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    contest = relationship("Contest", back_populates="contest_members")
    user = relationship("User")
    
    # Ensure a user can only be a member once per contest
    __table_args__ = (UniqueConstraint('contest_id', 'user_id', name='unique_contest_member'),) 