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
- [Project Structure](docs/project_structure.md) - Directory structure and organization

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

## Running in Production vs. Debug Mode (Backend)

The backend service in `docker-compose.yml` can be configured to run in either a debugging mode or a production-like mode.

### Debug Mode (Default in `docker-compose.yml`)

This mode is configured to:
1. Run `python scripts/create_admin.py setup`.
2. Start the `debugpy` debugger, listening on port `5678`.
3. **Wait for a debugger client** (e.g., from your IDE) to attach before fully starting the application.
4. Launch Uvicorn with `--reload` enabled for automatic code reloading on changes.

The command in `docker-compose.yml` looks like this:
```yaml
command: >
  sh -c "./wait-for-it.sh db:5432 --timeout=30 --strict -- \
  python scripts/create_admin.py setup && \
  python -m debugpy --wait-for-client --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```
To use this mode, you need to attach your IDE's debugger to port `5678` after starting the services with `docker-compose up`.

### Production-like Mode

This mode is configured to:
1. Run `python scripts/create_admin.py setup`.
2. Start Uvicorn directly without the debugger and without `--reload`.

To switch to this mode:
1. Open `docker-compose.yml`.
2. Comment out the entire `command:` block for the **DEBUGGING COMMAND**.
3. Uncomment the `command:` block for the **PRODUCTION-LIKE COMMAND**.

It should look like this after the change:
```yaml
    # COMMANDS - Choose one based on your needs:

    # 1. DEBUGGING COMMAND (current): 
    #    Starts the application with the debugpy debugger, waiting for a client to attach.
    #    Uvicorn will use --reload for automatic code reloading.
    # command: >
    #   sh -c "./wait-for-it.sh db:5432 --timeout=30 --strict -- \
    #   python scripts/create_admin.py setup && \
    #   python -m debugpy --wait-for-client --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

    # 2. PRODUCTION-LIKE COMMAND (commented out):
    #    Starts the application directly with Uvicorn. No debugger, no auto-reload.
    #    For true production, ensure DEBUG environment variables are also appropriately set to False.
    command: >
      sh -c "./wait-for-it.sh db:5432 --timeout=30 --strict -- \
      python scripts/create_admin.py setup && \
      uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

After making this change, rebuild and restart your services if necessary:
```bash
docker-compose up --build -d backend
# or simply
docker-compose up -d --force-recreate backend
```
Remember to also manage any `DEBUG` environment variables appropriately for a true production setting (e.g., set `DEBUG=False` in your `.env` file or directly in `docker-compose.yml` for the backend service if applicable).

## Frontend Development and Production

The frontend is a React application built with Vite and TypeScript. It supports both development and production modes with proper client-side routing.

### Development Mode

For development with hot reload and debugging:

```bash
# Using the convenience script
./scripts/dev.sh

# Or manually
docker-compose up --build
```

The frontend will be available at `http://localhost:3001` with:
- Hot reload enabled
- Source maps for debugging
- Proxy configuration for API calls to backend

### Production Mode

For production deployment with nginx:

```bash
# Using the convenience script
./scripts/prod.sh

# Or manually
docker-compose -f docker-compose.prod.yml up --build
```

The production build includes:
- Optimized React build
- nginx server for static file serving
- Proper client-side routing support
- Gzip compression
- Security headers
- Static asset caching

### URL Routing

Both development and production modes now properly support:
- Direct URL access (e.g., `localhost:3001/contests`, `localhost:3001/dashboard`)
- Browser back/forward navigation
- Dashboard tab URLs (e.g., `localhost:3001/dashboard?tab=texts`)

### Dashboard Tab Navigation

The dashboard supports URL-based tab navigation:
- `/dashboard` - Overview tab (default)
- `/dashboard?tab=contests` - My Contests tab
- `/dashboard?tab=texts` - My Texts tab
- `/dashboard?tab=agents` - AI Agents tab
- `/dashboard?tab=participation` - Participation tab
- `/dashboard?tab=credits` - Credits tab

When redirecting to a specific tab, use the format: `navigate('/dashboard?tab=texts')`

### Testing

To verify that all routing fixes are working correctly:

```bash
# Run automated tests
./scripts/test-all-routes.sh

# Or test individual components
curl http://localhost:3001/contests        # Should return 200 (React page)
curl http://localhost:3001/api/health      # Should return 200 (API proxy)
```

### Troubleshooting

If you encounter routing issues:

1. **500 errors on page routes**: Check that the Vite proxy configuration only handles `/api` routes
2. **API calls failing**: Verify that all API calls use the `/api` prefix in development
3. **Admin redirect issues**: Ensure the user has `is_admin: true` in their profile
4. **Tab not activating**: Check that the URL parameter format is correct (`?tab=tabname`)

### Architecture

- **Development**: Vite dev server with proxy for `/api` routes to backend
- **Production**: nginx serving static files with proxy for `/api` routes to backend
- **API calls**: All use `/api` prefix to avoid conflicts with React routes
- **Client-side routing**: React Router handles all page navigation
