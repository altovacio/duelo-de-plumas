from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo, model_validator
from typing import List, Optional, Any
from datetime import datetime

# --- Base Schemas ---
# Common fields for creation/update, inherit from BaseModel
class ModelBase(BaseModel):
    pass

# Common fields for reading, includes id + orm_mode
class ModelPublic(ModelBase):
    id: int
    
    class Config:
        from_attributes = True # Pydantic v2 alias for orm_mode

# --- User Schemas ---
class UserBase(ModelBase):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    # Role is now optional in base, will be set by endpoint logic or model default
    role: Optional[str] = Field(None, pattern=r'^(admin|judge|user)$') 
    # Judge type is optional, defaults to 'human' in model if not provided
    judge_type: Optional[str] = Field(None, pattern=r'^(human|ai)$') 

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Schema specifically for the /register endpoint request body
class UserRegister(ModelBase):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdate(ModelBase):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern=r'^(admin|judge|user)$')
    judge_type: Optional[str] = Field(None, pattern=r'^(human|ai)$')
    password: Optional[str] = Field(None, min_length=8) # Allow password update

# Public representation (omits password_hash)
class UserPublic(UserBase, ModelPublic): # Inherit from UserBase first
    pass # id is inherited from ModelPublic

# Detailed representation for admin or self (could include more)
class UserDetail(UserPublic):
    # Example: Add relationships if needed, ensure they use Public schemas
    # judged_contests: List['ContestPublic'] = [] # Avoid circular imports initially
    pass

# Schema for the /auth/users/me endpoint
class UserMe(ModelBase):
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

# --- NEW AIJudge Schemas ---
class AIJudgeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    ai_personality_prompt: str

class AIJudgeCreate(AIJudgeBase):
    pass

class AIJudgeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    ai_personality_prompt: Optional[str] = None

class AIJudgeRead(AIJudgeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }

# --- Token Schemas (for Authentication) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None # Store user ID in token payload
    scopes: List[str] = []

# --- Contest Schemas ---
class ContestBase(ModelBase):
    title: str = Field(..., max_length=150)
    description: Optional[str] = None
    start_date: Optional[datetime] = None # Optional on create, defaults in model
    end_date: Optional[datetime] = None
    status: str = Field('open', pattern=r'^(open|evaluation|closed)$')
    contest_type: str = Field('public', pattern=r'^(public|private)$')
    required_judges: int = Field(1, ge=1)
    # Add restriction fields
    restrict_judges_as_authors: bool = Field(False, description="Prevent assigned judges from submitting")
    limit_submissions_per_author: bool = Field(False, description="Limit each author to one submission")

class ContestCreate(ContestBase):
    password: Optional[str] = Field(None, min_length=6) # Password only if private

    @model_validator(mode='after')
    def check_password_required_for_private(self) -> 'ContestCreate':
        """Ensure password is provided if contest_type is 'private' (model validator)."""
        if self.contest_type == 'private' and self.password is None:
            raise ValueError('Password is required for private contests')
        return self

class ContestUpdate(ModelBase):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r'^(open|evaluation|closed)$')
    contest_type: Optional[str] = Field(None, pattern=r'^(public|private)$')
    required_judges: Optional[int] = Field(None, ge=1)
    password: Optional[str] = Field(None, min_length=6) # Allow password change
    # Add restriction fields
    restrict_judges_as_authors: Optional[bool] = None
    limit_submissions_per_author: Optional[bool] = None

class ContestPublic(ContestBase, ModelPublic):
    created_at: datetime
    updated_at: datetime

# Detailed view might include submissions, judges (using their public schemas)
class ContestDetail(ContestPublic):
    submissions: List['SubmissionRead'] = [] # Changed from SubmissionPublic
    human_judges: List[UserPublic] = [] # Renamed from judges
    ai_judges: List[AIJudgeRead] = [] # Added new relationship
    # ai_evaluations: List['AIEvaluationPublic'] = []

# --- Vote Schemas (Example) ---
class VoteBase(ModelBase):
    place: Optional[int] = Field(None, ge=1) # Rank (1st, 2nd, etc.)
    comment: Optional[str] = None
    submission_id: int
    # judge_id is implicitly set from the user making the request

class VoteCreate(VoteBase):
    pass # judge_id will be set from authenticated user

class VoteUpdate(ModelBase):
    place: Optional[int] = Field(None, ge=1)
    comment: Optional[str] = None

class VoteRead(VoteBase, ModelPublic): # Define VoteRead here
    timestamp: datetime
    app_version: str # Changed from Optional[str]
    judge_id: int # Add judge_id to the read model
    # Potentially include judge/submission info using Public schemas
    # judge: Optional[UserPublic] = None
    # submission: Optional[SubmissionPublic] = None # Avoid circular dependency for now
    model_config = {
        "from_attributes": True
    }

# --- Submission Schemas ---
class SubmissionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    text_content: str = Field(..., min_length=1)
    author_name: Optional[str] = Field(None, max_length=100) # If submission is anonymous or by non-user

class SubmissionCreate(SubmissionBase):
    # author_name is optional here, user_id will be set from authenticated user
    pass

class SubmissionRead(SubmissionBase):
    id: int
    contest_id: int
    user_id: Optional[int] # Submissions might not be linked to a user (e.g., AI generated?)
    submission_date: datetime
    word_count: int
    # Add missing fields from model
    total_points: int = 0 # Provide default if needed
    final_rank: Optional[int] = None
    is_ai_generated: bool = False # Provide default if needed
    ai_writer_id: Optional[int] = None
    
    votes: List[VoteRead] = [] # Include votes when reading a submission

    model_config = {
        "from_attributes": True
    }

# Response model specifically for the submission creation endpoint
class SubmissionCreateResponse(SubmissionBase): # Inherit from SubmissionBase
    id: int
    contest_id: int
    user_id: Optional[int]
    submission_date: datetime
    word_count: int
    # Exclude votes relationship for create response
    model_config = {
        "from_attributes": True
    }

class SubmissionUpdate(ModelBase):
    author_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=150)
    text_content: Optional[str] = None
    # Backend should handle updates to points/rank

class SubmissionPublic(SubmissionBase, ModelPublic):
    submission_date: datetime
    total_points: int
    final_rank: Optional[int] = None
    is_ai_generated: bool
    ai_writer_id: Optional[int] = None
    
class SubmissionDetail(SubmissionPublic):
    # votes: List['VotePublic'] = []
    # ai_writer: Optional['AIWriterPublic'] = None
    # ai_writing_request: Optional['AIWritingRequestPublic'] = None
    contest: ContestPublic # Include basic contest info

# --- AI Writer Schemas (Example) ---
class AIWriterBase(ModelBase):
    name: str = Field(..., max_length=64)
    description: Optional[str] = None
    personality_prompt: str

class AIWriterCreate(AIWriterBase):
    pass

class AIWriterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    personality_prompt: Optional[str] = None

class AIWriterPublic(AIWriterBase, ModelPublic):
    created_date: datetime # Note: Model has created_at, schema has created_date

AIWriterAdminView = AIWriterPublic

# --- NEW User-Owned AI Agent Schemas ---

class UserAIWriterBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=500)
    personality_prompt: str
    # base_prompt is not user-settable

class UserAIWriterCreate(UserAIWriterBase):
    pass # Inherits all fields from base

class UserAIWriterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=500)
    personality_prompt: Optional[str] = None

class UserAIWriterRead(UserAIWriterBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    # REMOVED: base_prompt
    # base_prompt: Optional[str] = None 

    model_config = {
        "from_attributes": True
    }

class UserAIJudgeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=500)
    personality_prompt: str
    # base_prompt is not user-settable

class UserAIJudgeCreate(UserAIJudgeBase):
    pass # Inherits all fields from base

class UserAIJudgeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=64)
    description: Optional[str] = Field(None, max_length=500)
    personality_prompt: Optional[str] = None

class UserAIJudgeRead(UserAIJudgeBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    # REMOVED: base_prompt
    # base_prompt: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

# --- ADDED: Contest Judge Assignment Schema ---
class AssignHumanJudgeRequest(BaseModel):
    # No extra fields needed for human judges yet
    pass

class AssignAIJudgeRequest(BaseModel):
    ai_model: str = Field(..., description="Required. Must match an ID from the configured AI models.")

# --- ADDED: Contest Status/Password Schemas ---
class ContestSetStatusRequest(BaseModel):
    status: str = Field(..., pattern=r'^(open|evaluation|closed)$')

class ContestResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)

# ADDED: Schema for checking contest password
class ContestCheckPasswordRequest(BaseModel):
    password: str

# --- ADDED: AI Evaluation Schemas ---
class AIEvaluationPublic(BaseModel):
    id: int
    contest_id: int
    judge_id: int 
    ai_model: str
    cost: float
    timestamp: datetime
    app_version: str
    # Exclude full_prompt and response_text from default public view
    class Config:
        from_attributes = True

class AIEvaluationDetail(AIEvaluationPublic):
    full_prompt: Optional[str] = None # Optional in case it was truncated or not stored
    response_text: str
    prompt_tokens: int
    completion_tokens: int
    # Potentially link to contest/judge public views
    # contest: Optional[ContestPublic] = None 
    # judge: Optional[UserPublic] = None 

# --- ADDED: AI Writer Submission Trigger Schema ---
class TriggerAISubmissionRequest(BaseModel):
    ai_writer_id: int = Field(..., description="ID of the AI Writer to use")
    model_id: str = Field(..., description="ID of the AI Model to use")
    title: str = Field(..., description="Title for the generated text", min_length=1, max_length=200)

# --- Placeholder Schemas for other models (Expand as needed) ---
# class AIEvaluationBase(ModelBase): ...

# ADDED: Public schema for AI Writing Requests
class AIWritingRequestPublic(BaseModel):
    id: int
    contest_id: int
    ai_writer_id: int
    submission_id: Optional[int] = None 
    ai_model: str
    # Exclude prompt/response text from public view
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost: Optional[float] = None
    timestamp: datetime
    app_version: str

    class Config:
        from_attributes = True

# ADDED: Schema for AI Costs Summary
class ModelCostSummary(BaseModel):
    model_name: str
    cost: float
    prompt_tokens: int
    completion_tokens: int

class AICostsSummary(BaseModel):
    total_cost: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    evaluation_cost: float = 0.0
    evaluation_prompt_tokens: int = 0
    evaluation_completion_tokens: int = 0
    writing_cost: float = 0.0
    writing_prompt_tokens: int = 0
    writing_completion_tokens: int = 0
    cost_by_model: List[ModelCostSummary] = []
    recent_evaluations: List[AIEvaluationPublic] = []
    recent_writing_requests: List[AIWritingRequestPublic] = []

# --- Update forward references ---
# This allows Pydantic to resolve the string references like 'ContestPublic'
# Do this at the end of the file
ContestDetail.model_rebuild()
SubmissionDetail.model_rebuild()
SubmissionRead.model_rebuild()
# VotePublic.model_rebuild()
# ... rebuild others as needed ... 