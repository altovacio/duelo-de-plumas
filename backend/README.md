# Duelo de Plumas - Backend

This is the API backend for Duelo de Plumas, a platform for literary contests with AI assistance.

## Current Version
This is in backend/app/core/config.py

## Development and Testing with Docker (Recommended)

The recommended way to develop, run, and test the backend is using Docker Compose. This ensures a consistent environment and simplifies database setup.

1.  **Prerequisites:**
    *   Ensure Docker and Docker Compose are installed and running on your system.
    *   (If on Windows with WSL) Ensure Docker Desktop is configured for WSL 2 integration.

2.  **Environment Configuration (`backend/.env`):**
    *   Navigate to the `backend/` directory.
    *   Create a `.env` file if it doesn't exist. You can copy `backend/.env.example` as a template.
    *   **Crucially, configure `backend/.env` to use the PostgreSQL database provided by Docker Compose.** The `docker-compose.yml` in the project root defines the database service. Your `DATABASE_URL` should be:
        ```
        DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/duelo_de_plumas
        ```
        (The username `postgres`, password `postgres`, service name `db`, and database `duelo_de_plumas` are defined in `docker-compose.yml`.)
    *   Fill in all other required variables in `.env` such as `SECRET_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

3.  **Build and Start Services:**
    *   All `docker-compose` commands should be run from the **project root directory** (the directory containing `docker-compose.yml`).
    *   To build the images (if necessary) and start the backend and database services:
        ```bash
        docker-compose up --build -d
        ```
    *   This command also automatically runs database migrations (`alembic upgrade head`) for the PostgreSQL database inside the container.

4.  **Running Tests:**
    *   With the services running, execute tests inside the `backend` container:
        ```bash
        docker-compose exec backend pytest
        ```
    *   Test results will be displayed in your terminal.

5.  **Accessing the API:**
    *   Once started, the API will be available at `http://localhost:8000`.
    *   API documentation (Swagger UI): `http://localhost:8000/docs`
    *   API documentation (ReDoc): `http://localhost:8000/redoc`

6.  **Stopping Services:**
    *   To stop the services when you're done:
        ```bash
        docker-compose down
        ```

7.  **Viewing Logs:**
    *   To view logs from the running services:
        ```bash
        docker-compose logs -f backend
        ```

## Native Python Setup (Alternative)

This section describes setting up and running the backend directly on your machine using a Python virtual environment.

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

4. Set up environment variables by creating a `.env` file in the backend directory.
   *Note: The example below uses SQLite, which is suitable for a simple native setup. For the Docker setup described above, you must configure PostgreSQL.*
   ```
   # Database configuration (SQLite example for native setup)
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

### Running Tests Natively
If you have set up the project natively with its dependencies installed in your virtual environment:
1. Ensure your `backend/.env` is configured (e.g., for SQLite as per the example, or a separate PostgreSQL instance if you manage it manually).
2. Ensure the test database is initialized and migrations are applied: `alembic upgrade head` (ensure `alembic.ini` and your `DATABASE_URL` are correctly pointing to your test DB).
3. Run tests using pytest:
   ```bash
   pytest
   ```
   (Run from the `backend` directory or configure your test runner accordingly).

## Running the API Natively

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