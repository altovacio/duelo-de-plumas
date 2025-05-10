from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class CreditTransactionBase(BaseModel):
    amount: int
    transaction_type: str  # "addition", "deduction"
    description: str


class CreditTransactionCreate(CreditTransactionBase):
    user_id: int
    ai_model: Optional[str] = None
    tokens_used: Optional[int] = None
    model_cost_rate: Optional[float] = None


class CreditTransactionResponse(CreditTransactionBase):
    id: int
    user_id: int
    created_at: datetime
    ai_model: Optional[str] = None
    tokens_used: Optional[int] = None
    model_cost_rate: Optional[float] = None

    class Config:
        orm_mode = True


class CreditTransactionFilter(BaseModel):
    user_id: Optional[int] = None
    transaction_type: Optional[str] = None
    ai_model: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class CreditUsageSummary(BaseModel):
    total_credits_used: int
    usage_by_model: Dict[str, int] = Field(default_factory=dict)
    usage_by_user: Dict[str, int] = Field(default_factory=dict)
    average_cost_per_operation: float
    total_tokens_used: int


class UserCreditUpdate(BaseModel):
    credits: int = Field(..., description="Amount of credits to add or remove")
    description: str = Field(..., description="Description of the credit update operation") 