# Database Schemas and Models

## Pydantic Schemas / Models

### User Models

```python
# Base User Model
class UserBase(BaseModel):
    username: str
    email: EmailStr
    
class UserCreate(UserBase):
    password: str
    
class UserResponse(UserBase):
    id: int
    is_admin: bool
    credits: int
    created_at: datetime
    
    class Config:
        orm_mode = True
        
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
class UserCredit(BaseModel):
    credits: int

# Credit Transaction Model
class CreditTransactionBase(BaseModel):
    amount: int
    transaction_type: str  # "addition", "deduction"
    description: str
    
class CreditTransactionCreate(CreditTransactionBase):
    user_id: int
    ai_model: Optional[str] = None
    tokens_used: Optional[int] = None
    
class CreditTransactionResponse(CreditTransactionBase):
    id: int
    user_id: int
    created_at: datetime
    ai_model: Optional[str] = None  # If transaction related to AI usage
    tokens_used: Optional[int] = None  # If transaction related to AI usage
    model_cost_rate: Optional[float] = None  # Cost per 1000 tokens if applicable
    
    class Config:
        orm_mode = True
        
class CreditTransactionFilter(BaseModel):
    user_id: Optional[int] = None
    transaction_type: Optional[str] = None
    ai_model: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
class CreditUsageSummary(BaseModel):
    total_credits_used: int
    usage_by_model: Dict[str, int]
    usage_by_user: Dict[int, int]
    average_cost_per_operation: float
    total_tokens_used: int

### Text Models

```python
class TextBase(BaseModel):
    title: str
    content: str  # Markdown content
    author: str  # This can be different from the owner
    
class TextCreate(TextBase):
    pass
    
class TextResponse(TextBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
class TextUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
```

### Contest Models

```python
class ContestBase(BaseModel):
    title: str
    description: str  # Markdown content
    is_private: bool = False
    password: Optional[str] = None  # Only required if is_private is True
    min_votes_required: Optional[int] = None
    
class ContestCreate(ContestBase):
    end_date: Optional[datetime] = None
    judge_restrictions: bool = False  # Whether judges can participate as text submitters
    owner_restrictions: bool = False  # Whether users can submit multiple texts
    
class ContestResponse(ContestBase):
    id: int
    creator_id: int
    state: str  # "open", "evaluation", "closed"
    created_at: datetime
    updated_at: datetime
    end_date: Optional[datetime] = None
    participant_count: int
    text_count: int
    
    class Config:
        orm_mode = True
        
class ContestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    password: Optional[str] = None
    min_votes_required: Optional[int] = None
    end_date: Optional[datetime] = None
    state: Optional[str] = None
```

### Contest Participation Models

```python
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
    user_id: int
    
class JudgeAssignmentResponse(BaseModel):
    contest_id: int
    judge_id: int
    assignment_date: datetime
    
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
    ranking: Optional[int] = None
    
    class Config:
        orm_mode = True
```

### Vote Models

```python
class VoteCreate(BaseModel):
    text_id: int
    text_place: Optional[int] = None  # Position (1 for 1st, 2 for 2nd, 3 for 3rd, null for non-podium)
    comment: str  # Justification/feedback
    is_ai_vote: bool = False
    ai_model: Optional[str] = None  # If is_ai_vote is True
    ai_version: Optional[str] = None  # If is_ai_vote is True
    
class VoteResponse(BaseModel): # Note: In the actual schema, VoteResponse inherits from a VoteBase that has text_place. For simplicity here, showing relevant fields.
    id: int
    text_id: int
    text_place: Optional[int] = None
    comment: str
    judge_id: int
    contest_id: int  # Each vote is for a text within a specific contest
    is_ai_vote: bool
    ai_model: Optional[str] = None
    ai_version: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True
```

### Agent Models (Judges and Writers)

```python
class AgentBase(BaseModel):
    name: str
    description: str
    prompt: str
    type: str  # "judge" or "writer"
    is_public: bool = False  # Only admins can create public agents
    
class AgentCreate(AgentBase):
    pass
    
class AgentResponse(AgentBase):
    id: int
    owner_id: int
    version: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    is_public: Optional[bool] = None
    
class AgentExecute(BaseModel):
    agent_id: int
    model: str
    contest_id: Optional[int] = None  # For judge agents
    title: Optional[str] = None      # For writer agents
    description: Optional[str] = None # For writer agents
    
class AgentExecutionResponse(BaseModel):
    id: int
    agent_id: int
    owner_id: int
    execution_type: str  # "judge" or "writer"
    status: str  # "completed" or "failed"
    result_id: Optional[int] = None  # ID of the resulting text or votes
    credits_used: int
    
    class Config:
        orm_mode = True
```

### Dashboard and Metrics Models

```python
class UserDashboard(BaseModel):
    author_contests: List[ContestResponse]
    judge_contests: List[ContestResponse]
    texts: List[TextResponse]
    credits: int
    pending_actions: List[str]
    
class AdminMetrics(BaseModel):
    total_users: int
    total_contests: int
    contests_by_state: Dict[str, int]
    top_winners: List[Tuple[str, int]]
    total_texts: int
    ai_usage: Dict[str, int]
    credits_allocated: int
    credits_used: int
```

## Project Structure

```
duelo-de-plumas/
│
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                 # FastAPI application initialization
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User management endpoints
│   │   │   ├── texts.py        # Text management endpoints
│   │   │   ├── contests.py     # Contest management endpoints
│   │   │   ├── votes.py        # Voting endpoints
│   │   │   ├── agents.py       # AI agent endpoints
│   │   │   ├── admin.py        # Admin-only endpoints
│   │   │   └── dashboard.py    # User dashboard endpoints
│   │   │
│   │   └── dependencies.py     # Shared route dependencies
│   │
│   ├── core/                   # Core application code
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   ├── security.py         # Authentication and permissions
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── db/                     # Database related code
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── text.py
│   │   │   ├── contest.py
│   │   │   ├── vote.py
│   │   │   ├── agent.py
│   │   │   ├── credit_transaction.py # Credit transaction tracking
│   │   │   ├── contest_text.py # Junction table for contest-text relationships
│   │   │   └── contest_judge.py # Junction table for contest-judge relationships
│   │   │
│   │   └── repositories/       # Database access logic
│   │       ├── __init__.py
│   │       ├── user_repository.py
│   │       ├── text_repository.py
│   │       ├── contest_repository.py
│   │       ├── vote_repository.py
│   │       ├── agent_repository.py
│   │       └── credit_repository.py
│   │
│   ├── schemas/                # Pydantic models for request/response
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── text.py
│   │   ├── contest.py
│   │   ├── vote.py
│   │   ├── agent.py
│   │   ├── credit.py
│   │   └── common.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── text_service.py
│   │   ├── contest_service.py
│   │   ├── vote_service.py
│   │   ├── agent_service.py
│   │   ├── ai_service.py       # Integration with AI models (OpenAI, etc.)
│   │   └── credit_service.py   # Credit management logic
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── markdown_utils.py   # Markdown processing
│       └── validation_utils.py # Input validation helpers
│
├── migrations/                 # Database migrations (Alembic)
│   ├── versions/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── alembic.ini
│
├── tests/                      # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_texts.py
│   │   ├── test_contests.py
│   │   ├── test_votes.py
│   │   └── test_agents.py
│   │
│   └── test_services/
│       ├── __init__.py
│       ├── test_auth_service.py
│       ├── test_user_service.py
│       └── ...
│
├── .env                        # Environment variables
├── .gitignore
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker configuration
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Alembic configuration
└── README.md                   # Project documentation
```

## Database Relationships

### Core Entity Relationships

1. **User**
   - Has many Texts (as owner)
   - Has many Contests (as creator)
   - Has many Votes (as judge)
   - Has many Agents (as owner)
   - Has many CreditTransactions
   - Can be assigned as a judge to multiple Contests (via Contest_Judge junction table)

2. **Text**
   - Belongs to a User (as owner)
   - Can belong to multiple Contests (via Contest_Text junction table)
   - Can receive multiple Votes (in the context of a Contest)
   - A text can be submitted to multiple contests and receive different votes in each contest

3. **Contest**
   - Belongs to a User (as creator)
   - Has many Texts (via Contest_Text junction table)
   - Has many assigned Judges (via Contest_Judge junction table)
   - Has many Votes
   - Can enforce restrictions (judges not participating as authors, authors submitting only one text)

4. **Vote**
   - Belongs to a User (as judge)
   - Belongs to a Contest
   - Belongs to a Text
   - A vote is specific to a text within a particular contest
   - Optional: Can be associated with an AI Agent

5. **Agent (AI Judge/Writer)**
   - Belongs to a User (as owner)
   - Has a type (judge or writer)
   - Executes synchronously

6. **CreditTransaction**
   - Belongs to a User
   - Records all credit changes (additions and deductions)
   - Tracks AI model used, tokens consumed, and cost rates
   - Maintains historical usage data
   - Enables detailed cost analysis and allocation

### Junction Tables

1. **Contest_Text**
   - Links Contests and Texts (many-to-many)
   - Records submission date
   - May include additional data like final ranking in the contest

2. **Contest_Judge**
   - Links Contests and Users as judges (many-to-many)
   - Records assignment date
   - Tracks whether the judge has completed their voting duties 