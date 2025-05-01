from datetime import datetime, timezone
from typing import List, Optional

# Use passlib for password hashing in the FastAPI version
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Table, Column, 
    UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

# Application version - can be sourced from config or kept here
# Consider moving to fastapi_config.py
APP_VERSION = "v1.02" # Keep consistent for now

# Define Base class using SQLAlchemy 2.0 syntax
class Base(AsyncAttrs, DeclarativeBase):
    pass

# Association table for Contest Judges (Many-to-Many)
# Define using SQLAlchemy Core Table object associated with Base metadata
contest_judges = Table(
    'contest_judges',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('contest_id', Integer, ForeignKey('contest.id'), primary_key=True),
    Column('ai_model', String(50), nullable=True) # Model used by this judge for this contest
)

# --- Model Definitions using SQLAlchemy 2.0 syntax ---

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True) # Set nullable=False? Ensure it's always set on creation.
    role: Mapped[str] = mapped_column(String(10), index=True, default='judge') # 'admin', 'judge', 'user'
    judge_type: Mapped[str] = mapped_column(String(10), default='human') # 'human' or 'ai'
    ai_personality_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships (adjust lazy loading, use Mapped)
    # Use back_populates for bidirectional relationships
    votes: Mapped[List["Vote"]] = relationship(back_populates='judge') # Removed lazy='dynamic' - default is select IN loading or use selectinload
    judged_contests: Mapped[List["Contest"]] = relationship(
        "Contest", secondary=contest_judges, back_populates='judges'
    )
    ai_evaluations: Mapped[List["AIEvaluation"]] = relationship(back_populates='judge') # Added back_populates

    # --- Methods using passlib --- 
    def set_password(self, password: str):
        """Hashes the password and sets the password_hash field."""
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies a given password against the stored hash."""
        return pwd_context.verify(password, self.password_hash)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_ai_judge(self) -> bool:
        return self.role == 'judge' and self.judge_type == 'ai'

    def __repr__(self):
        if self.is_ai_judge():
            return f'<AI Judge {self.username} ({self.judge_type})>'
        return f'<User {self.username} ({self.role})>'

# @login_manager.user_loader - Removed: Handled by FastAPI dependencies


class Contest(Base):
    __tablename__ = 'contest'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # Ensure timezone=True
    status: Mapped[str] = mapped_column(String(20), index=True, default='open') # 'open', 'evaluation', 'closed'
    contest_type: Mapped[str] = mapped_column(String(10), default='public') # 'public', 'private'
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    required_judges: Mapped[int] = mapped_column(Integer, default=1)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(back_populates='contest', cascade="all, delete-orphan")
    judges: Mapped[List["User"]] = relationship(
        "User", secondary=contest_judges, back_populates='judged_contests'
    )
    ai_evaluations: Mapped[List["AIEvaluation"]] = relationship(back_populates='contest', cascade="all, delete-orphan")

    # --- Methods using passlib --- 
    def set_password(self, password: str):
        """Hashes the password and sets the password_hash field if contest is private."""
        if self.contest_type == 'private':
            self.password_hash = pwd_context.hash(password)
        else:
            self.password_hash = None

    def check_password(self, password: str) -> bool:
        """Verifies a given password against the stored hash if contest is private."""
        if self.contest_type != 'private' or not self.password_hash:
            return False
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self):
        return f'<Contest {self.title}>'

class Submission(Base):
    __tablename__ = 'submission'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    submission_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey('contest.id'), nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_writer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('ai_writer.id'), nullable=True)
    
    # Relationships
    contest: Mapped["Contest"] = relationship(back_populates='submissions')
    votes: Mapped[List["Vote"]] = relationship(back_populates='submission', cascade="all, delete-orphan")
    ai_writer: Mapped[Optional["AIWriter"]] = relationship(back_populates='submissions')
    # Add relationship for AIWritingRequest if needed (one-to-one from Request to Submission)
    ai_writing_request: Mapped[Optional["AIWritingRequest"]] = relationship(back_populates='submission')


    def __repr__(self):
        return f'<Submission {self.title} by {self.author_name}>'

class Vote(Base):
    __tablename__ = 'vote'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    judge_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    submission_id: Mapped[int] = mapped_column(Integer, ForeignKey('submission.id'), nullable=False)
    app_version: Mapped[str] = mapped_column(String(10), default=APP_VERSION)
    
    # Relationships
    judge: Mapped["User"] = relationship(back_populates='votes')
    submission: Mapped["Submission"] = relationship(back_populates='votes')
    
    # UniqueConstraint - Can be defined in __table_args__
    # __table_args__ = (UniqueConstraint('judge_id', 'submission_id', name='_judge_submission_uc'),) 
    # Revisit if this constraint is truly needed or handled at application level

    def __repr__(self):
        return f'<Vote by Judge {self.judge_id} on Submission {self.submission_id} -> Place: {self.place}>'

class AIEvaluation(Base):
    __tablename__ = 'ai_evaluation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey('contest.id'), nullable=False)
    judge_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False) # This is the AI Judge User ID
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False)
    full_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    app_version: Mapped[str] = mapped_column(String(10), default=APP_VERSION)
    
    # Relationships
    contest: Mapped["Contest"] = relationship(back_populates='ai_evaluations')
    judge: Mapped["User"] = relationship(back_populates='ai_evaluations')
    
    def __repr__(self):
        return f'<AIEvaluation for Contest {self.contest_id} by Judge {self.judge_id}>'

class AIWriter(Base):
    __tablename__ = 'ai_writer'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    submissions: Mapped[List["Submission"]] = relationship(back_populates='ai_writer')
    ai_writing_requests: Mapped[List["AIWritingRequest"]] = relationship(back_populates='ai_writer') # Added relationship

    def __repr__(self):
        return f'<AIWriter {self.name}>'

class AIWritingRequest(Base):
    __tablename__ = 'ai_writing_request'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(Integer, ForeignKey('contest.id'), nullable=False)
    ai_writer_id: Mapped[int] = mapped_column(Integer, ForeignKey('ai_writer.id'), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False)
    full_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    # Made submission_id nullable=False initially, assuming request ALWAYS creates a submission? Check logic. If request can exist before submission is saved, keep nullable=True
    submission_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('submission.id'), nullable=True) 
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    app_version: Mapped[str] = mapped_column(String(10), default=APP_VERSION)
    
    # Relationships
    contest: Mapped["Contest"] = relationship() # No back_populates needed if Contest doesn't link back here directly
    ai_writer: Mapped["AIWriter"] = relationship(back_populates='ai_writing_requests')
    submission: Mapped[Optional["Submission"]] = relationship(back_populates='ai_writing_request')

    def __repr__(self):
        # Ensure ai_writer is loaded if needed for repr, or handle potential None
        writer_name = self.ai_writer.name if self.ai_writer else 'Unknown'
        return f'<AIWritingRequest for Contest {self.contest_id} by Writer {writer_name}>' 