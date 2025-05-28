from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    credits = Column(Integer, default=0, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    texts = relationship("Text", back_populates="owner", cascade="all, delete-orphan")
    contests = relationship("Contest", back_populates="creator", cascade="all, delete-orphan")
    contest_judges = relationship(
        "ContestJudge", 
        foreign_keys="ContestJudge.user_judge_id", 
        back_populates="user_judge",
        cascade="all, delete-orphan"
    )
    credit_transactions = relationship(
        "CreditTransaction", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="noload"
    )
    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")
    agent_executions = relationship("AgentExecution", back_populates="owner", cascade="all, delete-orphan") 