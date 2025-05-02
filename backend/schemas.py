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
    role: str = Field('judge', pattern=r'^(admin|judge|user)$')
    judge_type: Optional[str] = Field('human', pattern=r'^(human|ai)$')
    ai_personality_prompt: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(ModelBase):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern=r'^(admin|judge|user)$')
    judge_type: Optional[str] = Field(None, pattern=r'^(human|ai)$')
    ai_personality_prompt: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8) # Allow password update

# Public representation (omits password_hash)
class UserPublic(UserBase, ModelPublic): # Inherit from UserBase first
    pass # id is inherited from ModelPublic

# Detailed representation for admin or self (could include more)
class UserDetail(UserPublic):
    # Example: Add relationships if needed, ensure they use Public schemas
    # judged_contests: List['ContestPublic'] = [] # Avoid circular imports initially
    pass

# --- ADDED: Schemas specifically for Admin AI Judge CRUD ---
class AIJudgeCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)
    ai_personality_prompt: str # Prompt is required for AI judges
    # role is fixed to 'judge', judge_type is fixed to 'ai' on creation

class AIJudgeUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=64)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8) # Allow password update
    ai_personality_prompt: Optional[str] = None # Allow prompt update
    # role and judge_type should not be changed via this schema

# Use UserPublic for listing/viewing AI judges
AIJudgeAdminView = UserPublic 

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

class ContestPublic(ContestBase, ModelPublic):
    created_at: datetime
    updated_at: datetime

# Detailed view might include submissions, judges (using their public schemas)
class ContestDetail(ContestPublic):
    # Use forward references initially if needed
    submissions: List['SubmissionPublic'] = [] 
    judges: List[UserPublic] = []
    # ai_evaluations: List['AIEvaluationPublic'] = []

# --- Submission Schemas ---
class SubmissionBase(ModelBase):
    author_name: str = Field(..., max_length=100)
    title: str = Field(..., max_length=150)
    text_content: str
    contest_id: int # Required for linking
    # Omit fields calculated/set by backend (total_points, rank, date, ai info)

class SubmissionCreate(SubmissionBase):
    pass

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


# --- Vote Schemas (Example) ---
class VoteBase(ModelBase):
    place: Optional[int] = Field(None, ge=1) # Rank (1st, 2nd, etc.)
    comment: Optional[str] = None
    submission_id: int
    judge_id: int # Usually set from current_user

class VoteCreate(VoteBase):
    pass # judge_id will be set from authenticated user

class VoteUpdate(ModelBase):
    place: Optional[int] = Field(None, ge=1)
    comment: Optional[str] = None

class VotePublic(VoteBase, ModelPublic):
    timestamp: datetime
    app_version: str
    # Potentially include judge/submission info
    # judge: UserPublic
    # submission: SubmissionPublic # Careful with recursion

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
    created_date: datetime

# ADDED: Admin view might be the same as public for AI Writer
AIWriterAdminView = AIWriterPublic 

# --- ADDED: Contest Judge Assignment Schema ---
class AssignJudgeRequest(BaseModel):
    ai_model: Optional[str] = Field(None, description="Required if the judge is an AI judge. Must match an ID from the configured AI models.")

# --- ADDED: Contest Status/Password Schemas ---
class ContestSetStatusRequest(BaseModel):
    status: str = Field(..., pattern=r'^(open|evaluation|closed)$')

class ContestResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)

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
# class AIWritingRequestBase(ModelBase): ...
# class AIWritingRequestPublic(AIWritingRequestBase, ModelPublic): ...

# --- Update forward references ---
# This allows Pydantic to resolve the string references like 'ContestPublic'
# Do this at the end of the file
ContestDetail.model_rebuild()
SubmissionDetail.model_rebuild()
# VotePublic.model_rebuild()
# ... rebuild others as needed ... 