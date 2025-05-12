# Duelo de Plumas

A platform for literary contests with AI assistance.

## Current Version
**3.0.0**

## Environment Configuration

Environment variables are stored in `.env` files:
- `backend/.env` - For backend-specific configuration
- `frontend/.env` - For frontend-specific configuration (when implemented)

Each component has a corresponding `.env.example` file that shows the required variables.

## Documentation

All project documentation is available in the [docs](docs/) directory:

- [Project Description](docs/project_description.md) - Full project specification and requirements
- [API Plan](docs/duelo_de_plumas_api_plan.md) - API endpoints and implementation plan
- [Database Schemas and Models](docs/duelo_de_plumas_schemas_and_structure.md) - Database structure and Pydantic models
- [Project Structure](docs/project_structure.md) - Directory structure and organization
- [Implementation Status](docs/implementation_status.md) - Current implementation progress and deviations

## Backend: Development and Testing

The backend for Duelo de Plumas is located in the `backend/` directory. You have two primary ways to set up and run the backend and its tests:

1.  **Using Docker (Recommended):** This method uses Docker Compose to manage the backend service and a PostgreSQL database. It ensures a consistent environment and handles database setup automatically. This is the recommended approach for most development and all testing.
2.  **Native Python Setup:** You can also set up a local Python virtual environment and run the backend directly. This requires manual database setup (e.g., SQLite or your own PostgreSQL instance).

Full details for both methods can be found in `backend/README.md`.

### Quick Start: Running Tests with Docker

These instructions assume you are in the **project root directory**.

1.  **Prerequisites:**
    *   Ensure Docker and Docker Compose are installed and running.
    *   Navigate to `backend/` and create/configure your `.env` file based on `backend/.env.example`.
    *   **Crucially, set `DATABASE_URL` in `backend/.env` for PostgreSQL:**
        ```env
        DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/duelo_de_plumas
        ```
        (Ensure other necessary variables like `SECRET_KEY`, API keys, etc., are also set.)

2.  **Build and Start Services:**
    ```bash
    docker-compose up --build -d
    ```
    This starts the backend and database, and runs migrations.

3.  **Run Tests:**
    ```bash
    docker-compose exec backend pytest tests -x -v
    ```

4.  **Stop Services:**
    ```bash
    docker-compose down
    ```

For more detailed instructions, including native Python setup and running the API, please see [backend/README.md](backend/README.md).
