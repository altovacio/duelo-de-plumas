from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)  # Markdown content
    password_protected = Column(Boolean, default=False)  # Renamed from is_private
    password = Column(String, nullable=True)  # Only required if password_protected is True
    publicly_listed = Column(Boolean, default=True)  # New field for visibility in public listings
    min_votes_required = Column(Integer, nullable=True)
    status = Column(String, default="open")  # "open", "evaluation", "closed"
    judge_restrictions = Column(Boolean, default=False)  # Whether judges can participate as authors
    author_restrictions = Column(Boolean, default=False)  # Whether authors can submit multiple texts
    
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    creator = relationship("User", back_populates="contests")
    
    contest_texts = relationship("ContestText", foreign_keys="ContestText.contest_id", cascade="all, delete-orphan")
    contest_judges = relationship("ContestJudge", foreign_keys="ContestJudge.contest_id", cascade="all, delete-orphan")
    contest_members = relationship("ContestMember", foreign_keys="ContestMember.contest_id", cascade="all, delete-orphan")
    
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 