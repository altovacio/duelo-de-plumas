# Duelo de Plumas - Backend

This is the API backend for Duelo de Plumas, a platform for literary contests with AI assistance.

## Current Version
This is in backend/app/core/config.py

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file in the backend directory with the following content:
   ```
   # Database configuration
   DATABASE_URL=sqlite+aiosqlite:///./duelo_de_plumas.db

   # Security
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # AI configuration
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here

   # App settings
   DEBUG=True
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

   # Admin credentials (used by create_admin.py script if no arguments provided)
   ADMIN_USERNAME=admin
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=securepassword
   ```
   You can also copy the `.env.example` file and rename it to `.env`.

5. Initialize the database with migrations:
   ```
   alembic upgrade head
   ```

6. Create an admin user:
   
   You can create an admin user in two ways:
   
   a. By providing command line arguments:
   ```
   python scripts/create_admin.py <username> <email> <password>
   ```
   
   b. By using values from the `.env` file (recommended):
   ```
   python scripts/create_admin.py
   ```
   This will use the `ADMIN_USERNAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` values from your `.env` file.

## Running the API

Start the development server:
```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
│
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py             # FastAPI application initialization
│   │
│   ├── api/                # API routes
│   ├── core/               # Core application code
│   ├── db/                 # Database related code
│   ├── schemas/            # Pydantic models for request/response
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
│
├── migrations/             # Database migrations (Alembic)
├── scripts/                # Utility scripts
├── tests/                  # Backend tests
├── .env                    # Backend environment variables
├── .env.example            # Template for environment variables
├── alembic.ini             # Alembic configuration
└── requirements.txt        # Backend Python dependencies
```

## Development

### Creating a New Migration

After modifying the SQLAlchemy models, create a new migration:
```
alembic revision --autogenerate -m "Description of changes"
```

Then apply the migration:
```
alembic upgrade head
``` 