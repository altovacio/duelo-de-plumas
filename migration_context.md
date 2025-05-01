# Migration Context: Flask to FastAPI (Async)

This document summarizes the structure of the existing Flask application and outlines the plan for migrating it to FastAPI using an asynchronous database approach.

## I. Existing Flask Application Analysis

*   **Framework:** Flask
*   **Structure:** App Factory pattern (`create_app` in `app/__init__.py`), Blueprints (`main`, `auth`, `contest`, `admin`, `filters`).
*   **Entry Points:** `run.py`, `wsgi.py` (suggests Gunicorn usage).
*   **Database:**
    *   ORM: Flask-SQLAlchemy (`db = SQLAlchemy()`)
    *   Migrations: Flask-Migrate
    *   Schema (`app/models.py`): `User` (incl. AI judges), `Contest`, `Submission` (incl. AI writers), `Vote`, `AIEvaluation`, `AIWriter`, `AIWritingRequest`. Relational schema focused on contest management.
    *   Default DB: SQLite (`app.db`), configurable via `DATABASE_URL`.
*   **Authentication:** Flask-Login (`login_manager`), session-based. Role-based access (`admin`, `judge`). Custom decorators (`@judge_required`).
*   **Forms:** Flask-WTF (`app/contest/forms.py`, etc.).
*   **Templates:** Jinja2 (`app/templates/`), custom filters (`app/filters.py`), context processors (`app/__init__.py`).
*   **Static Files:** `app/static/`.
*   **Configuration:** `config.py` (using `python-dotenv` and environment variables), some hardcoded values.
*   **Dependencies (`requirements.txt`):** Flask stack, SQLAlchemy, Migrate, Login, WTF, Gunicorn, OpenAI, Anthropic, Tiktoken, python-dotenv, email-validator, Markdown.
*   **AI Integration:**
    *   Uses `openai` and `anthropic` clients.
    *   AI Judges (`User` model, `AIEvaluation` model, `app/services/ai_judge_service.py`).
    *   AI Writers (`AIWriter` model, `AIWritingRequest` model).
*   **Services:** Business logic potentially separated in `app/services/`.
*   **Deployment:** Likely using Gunicorn (`wsgi.py`, `requirements.txt`).

## II. Migration Plan to FastAPI (Async DB)

1.  **Project Setup:**
    *   New FastAPI project structure.
    *   `requirements.txt` update: Add `fastapi`, `uvicorn`, `pydantic[email]`, `jinja2`, `python-multipart`, `databases[asyncpg]` (or `databases[aiosqlite]`), `sqlalchemy` (for Core or ORM 2.0), `alembic`, `passlib[bcrypt]`. Keep AI clients, dotenv.
    *   Main app file (`main.py`).

2.  **Configuration (`fastapi_config.py` - User Request):**
    *   Use Pydantic `BaseSettings` for typed configuration from `.env`/environment variables.
    *   Separate settings for DB, API Keys, App secrets.

3.  **Database Layer (Async):**
    *   **Chosen Strategy:** Asynchronous.
    *   **Option 1:** Use `databases` library with SQLAlchemy Core and `asyncpg`/`aiosqlite`. Requires writing core SQL expressions.
    *   **Option 2 (Recommended):** Use SQLAlchemy 2.0+ native async support with `asyncpg`/`aiosqlite`. Allows closer ORM usage. Requires adapting models slightly and using async sessions (`AsyncSession`).
    *   Refactor all DB interactions (`routes.py`, `services/`) to use `async/await`.
    *   Adapt/configure Alembic (replaces Flask-Migrate) for async migrations if needed, or keep synchronous migration runs separate.

4.  **Models & Data Validation:**
    *   **DB Models:** Adapt existing SQLAlchemy models (`app/models.py`) for chosen async strategy (esp. for SQLAlchemy 2.0).
    *   **Pydantic Models:** Create Pydantic models for:
        *   API request bodies (e.g., `SubmissionCreate`, `LoginRequest`).
        *   API responses (e.g., `ContestPublic`, `UserPublic`, `SubmissionDetail`). Filter sensitive data.
        *   Configuration (`fastapi_config.py`).

5.  **Routing (`routers/`):**
    *   Replace Flask Blueprints with FastAPI `APIRouter`.
    *   Translate Flask routes (`@bp.route`) to FastAPI path operations (`@router.get`, etc.) with async function definitions (`async def`).
    *   Use type hints for path/query parameters.

6.  **Request Handling:**
    *   Replace Flask-WTF forms with:
        *   Pydantic models for API request bodies (JSON).
        *   FastAPI `Form()` dependencies for HTML form submissions (`python-multipart` needed).

7.  **Authentication & Authorization:**
    *   Replace Flask-Login with FastAPI `Depends`.
    *   Implement token-based auth (e.g., OAuth2 Password Bearer Flow with JWT).
    *   Create dependencies for `get_current_user`, `get_current_active_user`, permission checks (e.g., `require_admin`, `require_judge`).
    *   Use `passlib` for password hashing/verification.

8.  **Templates & Static Files:**
    *   Configure `Jinja2Templates` middleware.
    *   Mount `static/` using `StaticFiles`.
    *   Adapt `render_template` calls to use `templates.TemplateResponse`, passing `request: Request`.
    *   Replace context processors by explicitly adding data to the template context dictionary.

9.  **Services:**
    *   Refactor service functions to be `async def` if they perform DB operations or other I/O.
    *   Inject services using `Depends`.

10. **Dependencies & Lifecycle:**
    *   Manage DB connection pools using FastAPI startup/shutdown events or dependencies.
    *   Initialize AI clients similarly.

11. **Testing:**
    *   Use `httpx` and `pytest-asyncio` for async testing against the FastAPI app.

12. **Deployment:**
    *   Use `uvicorn` (potentially managed by Gunicorn) to serve the application.

## III. Next Steps

1.  Create `fastapi_config.py` using Pydantic `BaseSettings`.
2.  Set up basic FastAPI app structure (`main.py`, `routers/`).
3.  Adapt SQLAlchemy models (`models.py`) for async (SQLAlchemy 2.0 recommended).
4.  Configure Alembic for migrations.
5.  Implement async database session dependency.
6.  Start migrating the `auth` router/functionality (login, user loading, password hashing). 