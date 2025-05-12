from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, model_validator


class ContestBase(BaseModel):
    title: str
    description: str  # Markdown content
    is_private: bool = False
    password: Optional[str] = None  # Only required if is_private is True
    min_votes_required: Optional[int] = None


class ContestCreate(ContestBase):
    end_date: Optional[datetime] = None
    judge_restrictions: bool = False  # Whether judges can participate as authors
    author_restrictions: bool = False  # Whether authors can submit multiple texts


class ContestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    password: Optional[str] = None
    min_votes_required: Optional[int] = None
    end_date: Optional[datetime] = None
    state: Optional[str] = None  # "open", "evaluation", "closed"


class ContestResponse(ContestBase):
    id: int
    creator_id: int
    state: str  # "open", "evaluation", "closed"
    created_at: datetime
    updated_at: datetime
    end_date: Optional[datetime] = None
    judge_restrictions: bool
    author_restrictions: bool
    
    class Config:
        orm_mode = True


# For contest participant counts
class ContestDetailResponse(ContestResponse):
    participant_count: int
    text_count: int
    
    class Config:
        orm_mode = True


# For submitting texts to contests
class TextSubmission(BaseModel):
    text_id: int


class TextSubmissionResponse(BaseModel):
    contest_id: int
    text_id: int
    submission_date: datetime
    
    class Config:
        orm_mode = True


# For assigning judges to contests
class JudgeAssignment(BaseModel):
    user_id: Optional[int] = None
    agent_id: Optional[int] = None

    @model_validator(mode='after')
    def check_exactly_one_id_provided(cls, data):
        if (data.user_id is not None and data.agent_id is not None) or \
           (data.user_id is None and data.agent_id is None):
            raise ValueError('Exactly one of user_id or agent_id must be provided.')
        return data


class JudgeAssignmentResponse(BaseModel):
    assignment_id: int
    contest_id: int
    user_id: Optional[int] = None
    agent_id: Optional[int] = None
    assignment_date: datetime
    has_voted: Optional[bool] = None
    
    class Config:
        orm_mode = True


# For text details within a contest context
class ContestTextResponse(BaseModel):
    text_id: int
    title: str
    content: str
    # Author and owner details conditionally included based on contest state
    author: Optional[str] = None
    owner_id: Optional[int] = None
    ranking: Optional[int] = None  # 1 for first place, 2 for second, 3 for third, etc.
    
    class Config:
        orm_mode = True 