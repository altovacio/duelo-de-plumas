from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.db.models.user import User as UserModel
from app.services.text_service import TextService

router = APIRouter(
    tags=["texts"]
)


@router.post("/", response_model=TextResponse, status_code=status.HTTP_201_CREATED)
async def create_text(
    text_data: TextCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new text with the current user as owner.
    """
    service = TextService(db)
    return await service.create_text(text_data, current_user.id)


@router.get("/", response_model=List[TextResponse])
async def get_texts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    owner_id: Optional[int] = Query(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all texts, with optional filtering by owner.
    """
    service = TextService(db)
    if owner_id is not None:
        return await service.get_user_texts(owner_id, skip, limit)
    return await service.get_texts(skip, limit)


@router.get("/my", response_model=List[TextResponse])
async def get_my_texts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get texts belonging to the current user.
    """
    service = TextService(db)
    return await service.get_user_texts(current_user.id, skip, limit)


@router.get("/{text_id}", response_model=TextResponse)
async def get_text(
    text_id: int = Path(..., gt=0),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific text by ID.
    """
    service = TextService(db)
    return await service.get_text(text_id, current_user.id)


@router.put("/{text_id}", response_model=TextResponse)
async def update_text(
    text_data: TextUpdate,
    text_id: int = Path(..., gt=0),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a text. Only the owner or an admin can update a text.
    """
    service = TextService(db)
    return await service.update_text(text_id, text_data, current_user.id, current_user.is_admin)


@router.delete("/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_text(
    text_id: int = Path(..., gt=0),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a text. Only the owner or an admin can delete a text.
    """
    service = TextService(db)
    await service.delete_text(text_id, current_user.id, current_user.is_admin)
    return None 