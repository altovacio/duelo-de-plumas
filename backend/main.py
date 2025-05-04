from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
# ADD: Import StaticFiles and FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os # Needed for path joining

# Potentially import settings later
from .fastapi_config import settings

# Import routers
# from .routers import contest, auth # Old path
from .app.routers import contest, auth, ai_router # Corrected path
# ADD: Import the new main router
from .app.routers import main as main_router
# ADD: Import the new admin router
from .app.routers import admin as admin_router
# ADD: Import submission router
from .app.routers import submission # Use consistent path
# ADD: Import the new AI agents router
from .app.routers.ai_agents import writer_router, judge_router # NEW: Import specific routers
# ADD: Import the database module
from .database import init_db # Corrected relative import, removed close_db

# The app.routers path doesn't exist, fix it:
# from .app.routers.ai_router import router as ai_router  # This path is incorrect

# Fix the import path for the AI router - NO LONGER NEEDED WITH DIRECT IMPORT ABOVE
# try: # Remove complex try-except block again
#     from v2.app.routers.ai_router import router as ai_router
# except ImportError:
#     print("Warning: Could not import AI router from v2.app.routers.ai_router")
#     try:
#         from .app.routers.ai_router import router as ai_router
#     except ImportError:
#         print("Warning: Could not import AI router, skipping registration")
#         ai_router = None
# from .app.routers.ai_router import router as ai_router # Simplified import

# ADD: Get the absolute path to the project root (one level up from backend)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

app = FastAPI(
    title="Utopia API",
    description="API for the Duelo de Plumas collaborative writing platform.",
    version="0.2.0",
)

# CORS Middleware Configuration
origins = [
    "http://localhost:3000", # Allow frontend origin
    "http://127.0.0.1:3000",
    # Add other origins if needed (e.g., production frontend URL)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(contest.router, tags=["Contests"])
app.include_router(admin_router.router, prefix="/admin", tags=["Admin"])
app.include_router(submission.router, prefix="/submissions", tags=["Submissions"]) # ADDED submission router
app.include_router(ai_router.router, prefix="/ai", tags=["AI"])  # Include AI router directly
# ADD: Include the main router
app.include_router(main_router.router, prefix="/api/v2") # Main routes with prefix
# ADD: Include the admin router (typically with a distinct prefix)
app.include_router(admin_router.router) # Uses prefix '/admin' defined in the router itself

# Include the new user-owned AI agent router
app.include_router(writer_router) # NEW: Mount the writer router
app.include_router(judge_router) # NEW: Mount the judge router

# --- Static Files and Frontend Serving ---

# Mount static directories first -- REMOVE THESE
# Use check_dir=False because the directory might be outside the 'backend' package
# app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, 'css'), check_dir=False), name="css")
# app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, 'js'), check_dir=False), name="js")
# app.mount("/images", StaticFiles(directory=os.path.join(FRONTEND_DIR, 'images'), check_dir=False), name="images")

# Root endpoint to serve index.html -- REMOVE THIS
# @app.get("/", response_class=FileResponse)
# async def read_index():
#     index_path = os.path.join(FRONTEND_DIR, 'index.html')
#     if not os.path.exists(index_path):
#         return {"message": "index.html not found"} # Or raise HTTPException
#     return FileResponse(index_path)

# Catch-all route to serve index.html for client-side routing -- REMOVE THIS
# @app.get("/{full_path:path}", response_class=FileResponse)
# async def serve_frontend_app(full_path: str):
    # ... removed implementation ...
#     return FileResponse(index_path)

# ADD: Mount the entire frontend directory
# html=True allows serving index.html for / and other .html files directly
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True, check_dir=False), name="frontend")

# --- End Static Files and Frontend Serving ---


# Example for auth router later:
# from .routers import auth

# Add startup/shutdown events later if needed for DB connections etc.
# from .database import async_engine, init_db # Import engine/init function
# @app.on_event("startup")
# async def startup_event():
#     print("Starting up...")
#     # Optional: Create tables on startup (better handled by Alembic)
#     # await init_db()

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Shutting down...")
#     # Clean up resources like database engine 