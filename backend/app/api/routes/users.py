from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserCredit, UserPublicResponse, UserAdminResponse
from app.schemas.credit import CreditTransactionResponse
from app.services.user_service import UserService
from app.api.routes.auth import get_current_user, get_current_admin_user, get_optional_current_user
from app.db.models.user import User as UserModel
from app.db.models.contest import Contest as ContestModel
from app.services.contest_service import ContestService
from app.db.repositories.contest_repository import ContestRepository
from app.schemas.contest import ContestResponse

router = APIRouter(tags=["users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """Get current user details."""
    return current_user

@router.get("", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Get all users. Only administrators can access this endpoint.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    service = UserService(db)
    users = await service.get_users(skip, limit)
    return users

@router.get("/search", response_model=List[UserPublicResponse])
async def search_users(
    q: str = Query(..., min_length=2, description="Search query (username or email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Search users by username or email. Returns public user information only.
    Requires authentication to prevent abuse.
    """
    service = UserService(db)
    users = await service.search_users(q, limit)
    return users

@router.post("/by-ids", response_model=List[UserAdminResponse])
async def get_users_by_ids(
    user_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Get multiple users by their IDs. Returns user information including email.
    Only administrators can access this endpoint.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if len(user_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request more than 100 users at once"
        )
        
    service = UserService(db)
    users = await service.get_users_by_ids(user_ids)
    return users

@router.get("/judge-contests", response_model=List[ContestResponse])
async def get_judge_contests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get contests where the current user is a judge."""
    contest_repo = ContestRepository(db)
    contests = await contest_repo.get_contests_for_judge(current_user.id, skip, limit)
    return contests

@router.get("/author-contests", response_model=List[ContestResponse])
async def get_author_contests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get contests where the current user is an author (has submitted texts)."""
    contest_repo = ContestRepository(db)
    contests = await contest_repo.get_contests_for_author(current_user.id, skip, limit)
    return contests

@router.get("/{user_id}/public", response_model=UserPublicResponse)
async def get_user_public(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public user information (username only). 
    This endpoint is public and doesn't require authentication.
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    return user

@router.get("/{user_id}/credits/transactions", response_model=List[CreditTransactionResponse])
async def get_user_credit_transactions(
    user_id: int = Path(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get credit transactions for a specific user (admin only)."""
    from app.services.credit_service import CreditService
    
    transactions = await CreditService.get_user_transactions(db, user_id, skip, limit)
    return transactions

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update a user. Users can update themselves, admins can update anyone."""
    service = UserService(db)
    return await service.update_user(user_id, user_data, current_user)

@router.patch("/{user_id}/credits", response_model=UserResponse)
async def update_user_credits(
    user_id: int,
    credit_data: UserCredit,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Update a user's credits (admin only)."""
    service = UserService(db)
    return await service.update_user_credits(user_id, credit_data)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Delete a user (admin only)."""
    service = UserService(db)
    await service.delete_user(user_id)
    return {"message": "User deleted successfully"} 