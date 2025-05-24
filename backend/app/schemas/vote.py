from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    """Schema for creating a vote - contains actual database fields"""
    text_id: int = Field(..., description="ID of the text being voted on")
    text_place: Optional[int] = Field(None, description="Position (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")
    comment: str = Field(..., description="Justification/feedback for the vote")
    # For AI votes, these fields help determine the agent_execution_id
    is_ai_vote: bool = Field(False, description="Whether this is an AI-generated vote")
    ai_model: Optional[str] = Field(None, description="LLM model used for AI votes")


class VoteUpdate(BaseModel):
    """Schema for updating a vote"""
    text_place: Optional[int] = Field(None, description="Position (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")
    comment: Optional[str] = Field(None, description="Justification/feedback for the vote")


class VoteResponse(BaseModel):
    """Schema for vote responses - includes computed properties"""
    id: int
    contest_id: int
    text_id: int
    contest_judge_id: int
    agent_execution_id: Optional[int] = None
    text_place: Optional[int] = Field(None, description="Position (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")
    comment: str
    created_at: datetime
    
    # Computed properties from the Vote model
    judge_id: Optional[int] = Field(None, description="The actual judge ID (user_id for human votes, agent_id for AI votes)")
    is_ai_vote: bool = Field(default=False, description="Whether this is an AI-generated vote")
    ai_model: Optional[str] = Field(None, description="LLM model used for AI votes")
    ai_version: Optional[str] = Field(None, description="Version of the AI agent used")

    class Config:
        from_attributes = True 