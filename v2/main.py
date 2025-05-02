from fastapi import FastAPI

# Potentially import settings later
from .fastapi_config import settings

# Import routers
# from .routers import contest, auth # Old path
from .app.routers import contest, auth, ai_router # Corrected path
# ADD: Import the new main router
from .app.routers import main as main_router
# ADD: Import the new admin router
from .app.routers import admin as admin_router

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

app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    # Add other FastAPI app configurations here
)

# Placeholder root endpoint
@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(contest.router, prefix="/contests", tags=["Contests"])
app.include_router(ai_router.router, prefix="/ai", tags=["AI"])  # Include AI router directly
# ADD: Include the main router
app.include_router(main_router.router, prefix="/api/v2") # Main routes with prefix
# ADD: Include the admin router (typically with a distinct prefix)
app.include_router(admin_router.router) # Uses prefix '/admin' defined in the router itself

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