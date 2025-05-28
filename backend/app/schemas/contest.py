from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, model_validator

from app.schemas.vote import VoteEvaluationResponse

# Simple creator model for nested use
class ContestCreator(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True


class ContestBase(BaseModel):
    title: str
    description: str  # Markdown content
    password_protected: bool = False  # Renamed from is_private
    password: Optional[str] = None  # Only required if password_protected is True
    publicly_listed: bool = True  # New field for visibility in public listings
    min_votes_required: Optional[int] = None


class ContestCreate(ContestBase):
    end_date: Optional[datetime] = None
    judge_restrictions: bool = False  # Whether judges can participate as authors
    author_restrictions: bool = False  # Whether authors can submit multiple texts


class ContestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    password_protected: Optional[bool] = None  # Renamed from is_private
    password: Optional[str] = None
    publicly_listed: Optional[bool] = None  # New field
    min_votes_required: Optional[int] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None  # "open", "evaluation", "closed"
    judge_restrictions: Optional[bool] = None  # Whether judges can participate as authors
    author_restrictions: Optional[bool] = None  # Whether authors can submit multiple texts


# For assigning judges to contests
class JudgeAssignment(BaseModel):
    user_judge_id: Optional[int] = None
    agent_judge_id: Optional[int] = None

    @model_validator(mode='after')
    def check_exactly_one_id_provided(cls, data):
        if (data.user_judge_id is not None and data.agent_judge_id is not None) or \
           (data.user_judge_id is None and data.agent_judge_id is None):
            raise ValueError('Exactly one of user_judge_id or agent_judge_id must be provided.')
        return data


class JudgeAssignmentResponse(BaseModel):
    id: int
    contest_id: int
    user_judge_id: Optional[int] = None
    agent_judge_id: Optional[int] = None
    assignment_date: datetime
    has_voted: Optional[bool] = None
    
    # Additional fields for display purposes
    user_judge_name: Optional[str] = None      # Username for human judges  
    user_judge_email: Optional[str] = None     # Email for human judges
    agent_judge_name: Optional[str] = None     # Name for AI judges
    
    class Config:
        from_attributes = True


# For managing contest members
class ContestMemberAdd(BaseModel):
    user_id: int


class ContestMemberResponse(BaseModel):
    id: int
    contest_id: int
    user_id: int
    username: str  # User's username for display
    added_at: datetime
    
    class Config:
        from_attributes = True


class ContestResponse(ContestBase):
    id: int
    creator: ContestCreator  # Creator information - removed creator_id as it's redundant
    status: str  # "open", "evaluation", "closed"
    created_at: datetime
    updated_at: datetime
    end_date: Optional[datetime] = None
    judge_restrictions: bool
    author_restrictions: bool
    participant_count: int
    text_count: int
    has_password: bool  # Indicates if the contest is password protected
    
    class Config:
        from_attributes = True


# Now JudgeAssignmentResponse is defined before use here
class ContestDetailResponse(ContestResponse):
    judges: List[JudgeAssignmentResponse] = []
    members: List[ContestMemberResponse] = []  # New field for contest members
    # has_password inherited from ContestResponse
    
    class Config:
        from_attributes = True


# For submitting texts to contests
class TextSubmission(BaseModel):
    text_id: int


class TextSubmissionResponse(BaseModel):
    submission_id: int
    contest_id: int
    text_id: int
    submission_date: datetime
    
    class Config:
        from_attributes = True


# For text details within a contest context
class ContestTextResponse(BaseModel):
    id: int
    contest_id: int
    text_id: int
    submission_date: datetime
    title: str
    content: str
    # Author and owner details conditionally included based on contest state
    author: Optional[str] = None
    owner_id: Optional[int] = None
    ranking: Optional[int] = None  # 1 for first place, 2 for second, 3 for third, etc.
    total_points: Optional[int] = None  # Total points received in the contest
    evaluations: Optional[List[VoteEvaluationResponse]] = None
    
    class Config:
        from_attributes = True 