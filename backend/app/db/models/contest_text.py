from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from app.db.database import Base


class ContestText(Base):
    __tablename__ = "contest_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    text_id: Mapped[int] = mapped_column(Integer, ForeignKey("texts.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    contest = relationship("Contest", back_populates="contest_texts")
    text = relationship("Text", back_populates="contest_texts")
    
    submission_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Final ranking (null until contest is closed)
    ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    
    # Create a unique constraint so a text can't be submitted to the same contest multiple times
    __table_args__ = (
        Index("contest_text_unique", contest_id, text_id, unique=True),
    ) 