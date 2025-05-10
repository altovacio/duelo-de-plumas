from fastapi import APIRouter

from app.api.routes import auth, users, texts

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(texts.router) 