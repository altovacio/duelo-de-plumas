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
│   │   │   │   ├── votes.py    # Voting endpoints
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
│   │   │   │   ├── vote.py
│   │   │   │   ├── agent.py
│   │   │   │   ├── credit_transaction.py # Credit transaction tracking
│   │   │   │   ├── contest_text.py # Junction table for contest-text relationships
│   │   │   │   └── contest_judge.py # Junction table for contest-judge relationships
│   │   │   │
│   │   │   └── repositories/   # Database access logic
│   │   │       ├── __init__.py
│   │   │       ├── user_repository.py
│   │   │       ├── text_repository.py
│   │   │       ├── contest_repository.py
│   │   │       ├── vote_repository.py
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
│   │   │   ├── vote_service.py
│   │   │   ├── agent_service.py
│   │   │   ├── ai_service.py   # Integration with AI models (OpenAI, etc.)
│   │   │   └── credit_service.py # Credit management logic
│   │   │
│   │   └── utils/              # Utility functions
│   │       ├── __init__.py
│   │       ├── markdown_utils.py # Markdown processing
│   │       └── validation_utils.py # Input validation helpers
│   │
│   ├── migrations/             # Database migrations (Alembic)
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── alembic.ini
│   │
│   ├── tests/                  # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   │   ├── __init__.py
│   │   │   ├── test_auth.py
│   │   │   ├── test_users.py
│   │   │   ├── test_texts.py
│   │   │   ├── test_contests.py
│   │   │   ├── test_votes.py
│   │   │   └── test_agents.py
│   │   │
│   │   └── test_services/
│   │       ├── __init__.py
│   │       ├── test_auth_service.py
│   │       ├── test_user_service.py
│   │       └── ...
│   │
│   ├── .env                    # Backend environment variables
│   ├── Dockerfile              # Backend Docker configuration
│   ├── requirements.txt        # Backend Python dependencies
│   └── alembic.ini             # Alembic configuration
│
├── frontend/                   # Frontend application (placeholder)
│   ├── public/                 # Static files
│   ├── src/                    # Source code
│   │   ├── components/         # UI components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API service integrations
│   │   ├── styles/             # CSS/styling files
│   │   ├── utils/              # Utility functions
│   │   └── App.js              # Main application component
│   │
│   ├── package.json            # Frontend dependencies and scripts
│   └── .env                    # Frontend environment variables
│
├── docs/                       # Project documentation
│   ├── schemas_and_structure.md
│   ├── api_plan.md
│   ├── project_description.md
│   └── project_structure.md
│
├── .gitignore                  # Git ignore file
├── docker-compose.yml          # Docker Compose configuration for both services
├── README.md                   # Project documentation
└── .env.example                # Example environment variables
``` 