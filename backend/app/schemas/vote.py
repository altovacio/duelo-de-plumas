from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class VoteBase(BaseModel):
    text_id: int
    points: int = Field(..., description="3 for first place, 2 for second, 1 for third")
    comment: str = Field(..., description="Justification/feedback for the vote")
    

class VoteCreate(VoteBase):
    is_ai_vote: bool = False
    ai_model: Optional[str] = None
    ai_version: Optional[str] = None


class VoteResponse(VoteBase):
    id: int
    judge_id: int
    contest_id: int
    is_ai_vote: bool
    ai_model: Optional[str] = None
    ai_version: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True 