from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str
    description: str
    prompt: str
    type: str  # "judge" or "writer"
    is_public: bool = False


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    id: int
    owner_id: int
    version: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    is_public: Optional[bool] = None


class AgentExecuteJudge(BaseModel):
    agent_id: int
    model: str = Field(..., description="The LLM model to use for execution")
    contest_id: int = Field(..., description="The contest to judge")


class AgentExecuteWriter(BaseModel):
    agent_id: int
    model: str = Field(..., description="The LLM model to use for execution")
    title: Optional[str] = Field(None, description="Optional title for the generated text")
    description: Optional[str] = Field(None, description="Optional description/instructions for the generated text")


class AgentExecutionResponse(BaseModel):
    id: int
    agent_id: int
    owner_id: int
    execution_type: str  # "judge" or "writer"
    status: str  # "completed" or "failed"
    result_id: Optional[int] = None  # ID of the resulting text or votes
    credits_used: int
    created_at: datetime

    class Config:
        from_attributes = True 