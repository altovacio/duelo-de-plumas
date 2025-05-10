from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class CreditTransaction(Base):
    """Model for tracking user credit transactions."""
    
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)  # Positive for additions, negative for deductions
    transaction_type = Column(String, nullable=False)  # "addition", "deduction"
    description = Column(String, nullable=False)
    ai_model = Column(String, nullable=True)  # If transaction related to AI usage
    tokens_used = Column(Integer, nullable=True)  # If transaction related to AI usage
    model_cost_rate = Column(Float, nullable=True)  # Cost per 1000 tokens if applicable
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="credit_transactions") 