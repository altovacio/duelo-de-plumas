from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class VoteBase(BaseModel):
    text_id: int
    text_place: Optional[int] = Field(None, description="Position (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")
    comment: str = Field(..., description="Justification/feedback for the vote")
    

class VoteCreate(VoteBase):
    # Allow frontend to send 'place' instead of 'text_place' for compatibility
    place: Optional[int] = Field(None, description="Alias for text_place (frontend compatibility)")
    is_ai_vote: bool = False
    agent_id: Optional[int] = Field(None, description="Agent ID for AI votes (required when is_ai_vote=True)")
    ai_model: Optional[str] = None
    ai_version: Optional[str] = None
    
    def __init__(self, **data):
        # If place is provided but text_place is not, use place for text_place
        if 'place' in data and data['place'] is not None and 'text_place' not in data:
            data['text_place'] = data['place']
        elif 'place' in data and data['place'] is not None and data.get('text_place') is None:
            data['text_place'] = data['place']
        super().__init__(**data)


class VoteResponse(VoteBase):
    id: int
    judge_id: int
    contest_id: int
    is_ai_vote: bool
    ai_model: Optional[str] = None
    ai_version: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 