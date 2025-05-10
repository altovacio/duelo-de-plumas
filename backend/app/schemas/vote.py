from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class VoteBase(BaseModel):
    text_id: int
    text_place: Optional[int] = Field(None, description="Position (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")
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