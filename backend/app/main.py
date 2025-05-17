from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers
from app.api.routes import auth, users, texts, contests, votes, admin, dashboard, agents
# Import other routers as they become available

from app.core.config import settings

app = FastAPI(
    title="Duelo de Plumas API",
    description="API for literary contests with AI assistance",
    version=settings.VERSION
)

# CORS Configuration
origins = settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_debug_middleware(request, call_next):
    # For debugging - log any server errors
    response = await call_next(request)
    if response.status_code >= 500:
        print(f"5XX Error occurred: {request.method} {request.url.path} - Status {response.status_code}")
    return response

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(texts.router, prefix="/texts", tags=["texts"])
app.include_router(contests.router, prefix="/contests", tags=["contests"])
app.include_router(votes.router, prefix="", tags=["votes"])  # Note: votes endpoints are at /contests/{contest_id}/votes
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
# Include other routers as they become available

@app.get("/")
async def root():
    return {"message": "Welcome to Duelo de Plumas API"}

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 