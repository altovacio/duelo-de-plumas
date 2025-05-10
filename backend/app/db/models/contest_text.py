from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ContestText(Base):
    __tablename__ = "contest_texts"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    text_id = Column(Integer, ForeignKey("texts.id", ondelete="CASCADE"), nullable=False)
    
    # Contest relationship defined in Contest model
    # Text relationship defined in Text model
    
    submission_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Final ranking (null until contest is closed)
    ranking = Column(Integer, nullable=True)
    
    # Create a unique constraint so a text can't be submitted to the same contest multiple times
    __table_args__ = (
        Index("contest_text_unique", contest_id, text_id, unique=True),
    ) 