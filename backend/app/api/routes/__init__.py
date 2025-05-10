from fastapi import APIRouter

from app.api.routes import auth, users, texts, contests, votes, admin, dashboard, agents

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(texts.router)
api_router.include_router(contests.router)
api_router.include_router(votes.router)
api_router.include_router(admin.router)
api_router.include_router(dashboard.router)
api_router.include_router(agents.router) 