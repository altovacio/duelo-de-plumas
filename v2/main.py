from fastapi import FastAPI

# Potentially import settings later
from .fastapi_config import settings

# Import routers
from .routers import contest

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
app.include_router(contest.router, prefix="/contests", tags=["Contests"])
# Example for auth router later:
# from .routers import auth
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

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
#     await async_engine.dispose() 