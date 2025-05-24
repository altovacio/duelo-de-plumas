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


class VoteEvaluationResponse(BaseModel):
    """Simplified schema for displaying vote evaluations in contest results"""
    comment: Optional[str] = None
    judge_identifier: Optional[str] = None
    text_place: Optional[int] = Field(None, description="Position given by this judge (1 for 1st place, 2 for 2nd place, 3 for 3rd place, null for non-podium texts)")

    class Config:
        from_attributes = True


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
    
    # Computed properties (set by factory method)
    judge_id: Optional[int] = Field(None, description="The actual judge ID (user_id for human votes, agent_id for AI votes)")
    is_ai_vote: bool = Field(default=False, description="Whether this is an AI-generated vote")
    ai_model: Optional[str] = Field(None, description="LLM model used for AI votes")
    ai_version: Optional[str] = Field(None, description="Version of the AI agent used")

    @classmethod
    async def from_vote_details(cls, vote_details: dict) -> "VoteResponse":
        """Factory method to create VoteResponse from vote details dict"""
        return cls(
            id=vote_details["id"],
            contest_id=vote_details["contest_id"],
            text_id=vote_details["text_id"],
            contest_judge_id=vote_details.get("contest_judge_id"),  # This might need to be added to vote_details
            agent_execution_id=vote_details.get("agent_execution_id"),
            text_place=vote_details.get("text_place"),
            comment=vote_details["comment"],
            created_at=vote_details["created_at"],
            judge_id=vote_details.get("judge_id"),
            is_ai_vote=vote_details.get("is_ai_vote", False),
            ai_model=vote_details.get("ai_model"),
            ai_version=vote_details.get("ai_version")
        )

    @classmethod
    def from_vote_model(cls, vote, judge_id: Optional[int] = None, is_ai_vote: bool = False, 
                       ai_model: Optional[str] = None, ai_version: Optional[str] = None) -> "VoteResponse":
        """Factory method to create VoteResponse from Vote model with computed values"""
        return cls(
            id=vote.id,
            contest_id=vote.contest_id,
            text_id=vote.text_id,
            contest_judge_id=vote.contest_judge_id,
            agent_execution_id=vote.agent_execution_id,
            text_place=vote.text_place,
            comment=vote.comment,
            created_at=vote.created_at,
            judge_id=judge_id,
            is_ai_vote=is_ai_vote,
            ai_model=ai_model,
            ai_version=ai_version
        ) 