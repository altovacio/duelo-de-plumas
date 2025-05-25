from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Index
from sqlalchemy.sql import func
from app.db.database import Base

class AIDebugLog(Base):
    """
    Simple debug logging table for AI operations (development only).
    Tracks what we send to LLM and what we receive back.
    """
    __tablename__ = "ai_debug_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    operation_type = Column(String(20), nullable=False)  # 'writer' or 'judge'
    
    # Basic context
    user_id = Column(Integer, nullable=True)
    agent_id = Column(Integer, nullable=True)
    contest_id = Column(Integer, nullable=True)  # for judge operations
    model_id = Column(String(100), nullable=True)
    
    # What we send to LLM
    strategy_input = Column(Text, nullable=True)  # Variables passed to strategy
    llm_prompt = Column(Text, nullable=True)      # Actual prompt sent to LLM
    
    # What we get back
    llm_response = Column(Text, nullable=True)    # Raw LLM response
    parsed_output = Column(Text, nullable=True)   # What we extracted/parsed
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 6), nullable=True)

    # Index for timestamp-based queries
    __table_args__ = (
        Index('idx_ai_debug_timestamp', 'timestamp'),
    ) 