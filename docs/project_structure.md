# Duelo de Plumas - Project Structure

```
duelo-de-plumas/
│
├── backend/                    # Backend code
│   ├── app/                    # Main application package
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application initialization
│   │   │
│   │   ├── api/                # API routes
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py     # Authentication endpoints
│   │   │   │   ├── users.py    # User management endpoints
│   │   │   │   ├── texts.py    # Text management endpoints
│   │   │   │   ├── contests.py # Contest management endpoints
│   │   │   │   ├── votes.py    # Voting endpoints (supports multi-vote system)
│   │   │   │   ├── agents.py   # AI agent endpoints
│   │   │   │   ├── admin.py    # Admin-only endpoints
│   │   │   │   └── dashboard.py # User dashboard endpoints
│   │   │   │
│   │   │   └── dependencies.py # Shared route dependencies
│   │   │
│   │   ├── core/               # Core application code
│   │   │   ├── __init__.py
│   │   │   ├── config.py       # Configuration settings
│   │   │   ├── security.py     # Authentication and permissions
│   │   │   └── exceptions.py   # Custom exceptions
│   │   │
│   │   ├── db/                 # Database related code
│   │   │   ├── __init__.py
│   │   │   ├── database.py     # Database connection
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── text.py
│   │   │   │   ├── contest.py
│   │   │   │   ├── vote.py     # Enhanced to support multiple votes by same judge
│   │   │   │   ├── agent.py
│   │   │   │   ├── agent_execution.py # Tracks AI agent executions
│   │   │   │   ├── credit_transaction.py # Credit transaction tracking
│   │   │   │   ├── contest_text.py # Junction table for contest-text relationships
│   │   │   │   └── contest_judge.py # Junction table for contest-judge relationships
│   │   │   │
│   │   │   └── repositories/   # Database access logic
│   │   │       ├── __init__.py
│   │   │       ├── user_repository.py
│   │   │       ├── text_repository.py
│   │   │       ├── contest_repository.py
│   │   │       ├── vote_repository.py # Updated for AI and human vote management
│   │   │       ├── agent_repository.py
│   │   │       └── credit_repository.py
│   │   │
│   │   ├── schemas/            # Pydantic models for request/response
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── text.py
│   │   │   ├── contest.py
│   │   │   ├── vote.py
│   │   │   ├── agent.py
│   │   │   ├── credit.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/           # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── text_service.py
│   │   │   ├── contest_service.py
│   │   │   ├── vote_service.py # Enhanced to handle multiple vote types
│   │   │   ├── agent_service.py
│   │   │   ├── ai_service.py   # Integration with AI models (OpenAI, etc.) - Now uses strategies
│   │   │   ├── ai_provider_service.py  # Specific AI provider implementations
│   │   │   ├── ai_strategies/  # NEW: Directory for AI execution strategies
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_strategy.py       # Strategy interfaces
│   │   │   │   ├── writer_strategies.py   # Concrete writer strategies
│   │   │   │   └── judge_strategies.py    # Concrete judge strategies
│   │   │   └── credit_service.py # Credit management logic
│   │   │
│   │   └── utils/              # Utility functions
│   │       ├── __init__.py
│   │       ├── markdown_utils.py # Markdown processing
│   │       ├── validation_utils.py # Input validation helpers
│   │       ├── ai_models.py    # AI model configuration utilities
│   │       ├── judge_prompts.py # AI Judge prompt structures
│   │       ├── writer_prompts.py # AI Writer prompt structures
│   │       └── ai_model_costs.json # AI model definitions and pricing
│   │
│   ├── migrations/             # Database migrations (Alembic)
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── alembic.ini
│   │
│   ├── scripts/                # Utility scripts for setup and maintenance
│   │   └── create_admin.py     # Script to create admin user and database tables
│   │
│   ├── tests/                  # Backend tests
│   │   ├── __init__.py         # Makes 'tests' a Python package (NEW)
│   │   ├── conftest.py         # Pytest fixtures and shared E2E helpers
│   │   ├── shared_test_state.py # Shared state for E2E tests (e.g., test_data dict)
│   │   ├── e2e_test_plan_config.py # Stores the main E2E test plan string
│   │   │
│   │   ├── debug_tests/        # Simplified tests for debugging (NEW)
│   │   │   ├── __init__.py     # Makes 'debug_tests' a Python package (NEW)
│   │   │   └── test_simple_auth.py # Basic auth tests (NEW)
│   │   │
│   │   ├── e2e_sec_01_setup_user_registration.py
│   │   ├── e2e_sec_02_ai_agent_creation.py
│   │   ├── e2e_sec_03_contest_creation_management.py
│   │   ├── e2e_sec_04_text_creation.py
│   │   ├── e2e_sec_05_text_submission.py
│   │   ├── e2e_sec_06_evaluation_phase.py
│   │   ├── e2e_sec_07_contest_closure_results.py
│   │   ├── e2e_sec_08_cost_usage_monitoring_pre_cleanup.py
│   │   ├── e2e_sec_09_cleanup_routine.py
│   │   └── e2e_sec_10_final_state_verification_post_cleanup.py
│   │
│   ├── .env                    # Backend environment variables
│   ├── .env.example            # Template for environment variables
│   ├── Dockerfile              # Backend Docker configuration
│   ├── requirements.txt        # Backend Python dependencies
│   ├── README.md               # Backend specific documentation
│   └── alembic.ini             # Alembic configuration
│   └── pytest.ini              # Pytest configuration (e.g., test file patterns) (NEW)
│
├── frontend/                   # Frontend application
│   ├── public/                 # Static assets
│   │   ├── index.html          # HTML template
│   │   └── assets/             # Images, icons, etc.
│   │
│   ├── src/                    # Source code
│   │   ├── components/         # Reusable UI components
│   │   │   ├── Layout/         # App-level layout (Header, Footer, MainLayout)
│   │   │   ├── auth/           # Authentication related components (e.g., ProtectedRoute)
│   │   │   ├── Contest/        # Contest specific components (e.g. ContestCard, TextSubmissionForm, HumanJudgingForm, AIJudgeExecutionForm, ContestResults, JudgingForm (planned))
│   │   │   ├── TextEditor/     # Markdown editor component for text input (e.g. wrapper for react-md-editor)
│   │   │   ├── MarkdownEditor/ # Generic Markdown rendering component (planned, distinct from TextEditor for input)
│   │   │   ├── TextSelectionModal/ # Modal for selecting texts (planned)
│   │   │   └── AgentControls/  # UI for running AI agents (judge/writer)
│   │   │
│   │   ├── pages/              # Page components (views)
│   │   │   ├── Home/           # Landing page (highlights, welcome)
│   │   │   ├── ContestList/    # All contests listing
│   │   │   ├── ContestDetail/  # Detail for a specific contest
│   │   │   ├── Dashboard/      # User workspace (texts, agents, credits)
│   │   │   ├── Auth/           # Login & Register pages (LoginPage.tsx, RegistrationPage.tsx)
│   │   │   └── Admin/          # Admin panels (user mgmt, global AI agents)
│   │   │
│   │   ├── services/           # API integration (calls to FastAPI)
│   │   │   ├── authService.ts  # Authentication services (exports apiClient instance)
│   │   │   ├── contestService.ts
│   │   │   ├── textService.ts
│   │   │   ├── agentService.ts
│   │   │   └── creditService.ts
│   │   │
│   │   ├── hooks/              # Custom React hooks (e.g., useFetch)
│   │   │   ├── useAuth.ts      # Authentication hooks
│   │   │   ├── useCredits.ts   # Credit management hooks
│   │   │   └── useMultiVote.ts # Hooks for handling multiple vote types
│   │   │
│   │   ├── contexts/           # React Context providers (e.g., ThemeContext)
│   │   ├── store/              # Global state management (e.g., Zustand stores like authStore.ts)
│   │   ├── types/              # TypeScript type definitions (e.g., auth.ts)
│   │   ├── utils/              # Utility functions (markdown parsing, formatting)
│   │   │   ├── markdownUtils.ts
│   │   │   ├── creditUtils.ts  # Credit calculation helpers
│   │   │   └── formatters.ts   # Date/time/number formatters
│   │   │
│   │   ├── styles/             # Global styles, theme definitions
│   │   ├── App.tsx             # Application root
│   │   ├── index.tsx           # Entry point
│   │   └── vite-env.d.ts     # Vite client TypeScript environment definitions
│   │
│   ├── package.json            # Frontend dependencies and scripts
│   ├── tsconfig.json           # TypeScript config (if TS)
│   ├── .env                    # Frontend environment variables
│   └── README.md               # Frontend-specific instructions
│
├── docs/                       # Project documentation
│   ├── project_description.md
│   ├── project_structure.md
│   ├── implementation_plan.md
│   ├── front_implementation_plan.md
│   └── implementation_status.md
│
├── examples/                  # Example text files
│
├── .gitignore                  # Git ignore file
├── docker-compose.yml          # Docker Compose configuration for both services
└── README.md                   # Project documentation
``` 