from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserCredit, UserPublicResponse
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

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific user. Users can view their own details, administrators can view all.
    """
    # Check permissions (users can only see their own details, admins can see all)
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    service = UserService(db)
    user = await service.get_user(user_id)
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a user. Users can only update their own details, administrators can update all.
    """
    service = UserService(db)
    user = await service.update_user(user_id, user_data, current_user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Delete a user. Only administrators can delete users.
    """
    service = UserService(db)
    await service.delete_user(user_id, current_user)
    return None

@router.patch("/{user_id}/credits", response_model=UserResponse)
async def update_user_credits(
    user_id: int,
    credit_data: UserCredit,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """
    Update a user's credits. Only administrators can update user credits.
    """
    service = UserService(db)
    user = await service.update_user_credits(user_id, credit_data, current_user)
    return user

@router.get("/judge-contests", response_model=List[ContestResponse])
async def get_user_judge_contests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all contests where the current user is a judge.
    """
    contests = await ContestService.get_contests_where_user_is_judge(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Transform the Contest models to ContestResponse
    response_list = []
    for contest_orm in contests:
        # Fetch details including counts for each contest
        contest_data_with_counts = await ContestRepository.get_contest_with_counts(db=db, contest_id=contest_orm.id)
        if contest_data_with_counts:
            # Reflect whether a password is set on each contest
            contest_data_with_counts['has_password'] = bool(contest_data_with_counts.get('password'))
            response_list.append(ContestResponse.model_validate(contest_data_with_counts))
    
    return response_list 