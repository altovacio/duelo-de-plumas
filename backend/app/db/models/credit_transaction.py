from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class CreditTransaction(Base):
    """Model for tracking user credit transactions."""
    
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Integer, nullable=False)  # Positive for additions, negative for deductions
    transaction_type = Column(String, nullable=False)  # "purchase", "consumption", "refund", "admin_adjustment"
    description = Column(String, nullable=False)
    ai_model = Column(String, nullable=True)  # If transaction related to AI usage
    tokens_used = Column(Integer, nullable=True)  # If transaction related to AI usage
    real_cost_usd = Column(Float, nullable=True)  # Actual cost in USD calculated using estimate_cost_usd
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship with User (lazy loaded by default)
    user = relationship(
        "User", 
        back_populates="credit_transactions",
        foreign_keys=[user_id],
        lazy="noload"  # Don't load by default to avoid N+1 queries
    ) 