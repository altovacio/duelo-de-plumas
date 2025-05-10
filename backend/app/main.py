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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(texts.router, prefix="/texts", tags=["Texts"])
app.include_router(contests.router, prefix="/contests", tags=["Contests"])
app.include_router(votes.router, prefix="", tags=["Votes"])  # Note: votes endpoints are at /contests/{contest_id}/votes
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
# Include other routers as they become available
# app.include_router(agents.router, prefix="/agents", tags=["AI Agents"])

@app.get("/")
async def root():
    return {"message": "Welcome to Duelo de Plumas API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 