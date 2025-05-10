from typing import List
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.schemas.user import UserResponse
from app.services import text_service

router = APIRouter(
    prefix="/texts",
    tags=["texts"]
)


@router.post("/", response_model=TextResponse, status_code=status.HTTP_201_CREATED)
def create_text(
    text_data: TextCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new text with the current user as owner.
    """
    return text_service.create_text(db, text_data, current_user.id)


@router.get("/", response_model=List[TextResponse])
def get_texts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    owner_id: int = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all texts, with optional filtering by owner.
    """
    if owner_id is not None:
        return text_service.get_user_texts(db, owner_id, skip, limit)
    return text_service.get_texts(db, skip, limit)


@router.get("/my", response_model=List[TextResponse])
def get_my_texts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get texts belonging to the current user.
    """
    return text_service.get_user_texts(db, current_user.id, skip, limit)


@router.get("/{text_id}", response_model=TextResponse)
def get_text(
    text_id: int = Path(..., gt=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific text by ID.
    """
    return text_service.get_text(db, text_id, current_user.id)


@router.put("/{text_id}", response_model=TextResponse)
def update_text(
    text_data: TextUpdate,
    text_id: int = Path(..., gt=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a text. Only the owner or an admin can update a text.
    """
    return text_service.update_text(db, text_id, text_data, current_user.id, current_user.is_admin)


@router.delete("/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_text(
    text_id: int = Path(..., gt=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a text. Only the owner or an admin can delete a text.
    """
    text_service.delete_text(db, text_id, current_user.id, current_user.is_admin)
    return None 