from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.routes.auth import get_current_admin_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.credit import UserCreditUpdate, CreditTransactionResponse, CreditUsageSummary, CreditTransactionFilter
from app.services.user_service import UserService
from app.services.credit_service import CreditService
from app.db.models.user import User as UserModel
from datetime import datetime

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get all users (admin only)."""
    user_service = UserService(db)
    return await user_service.get_users(skip=skip, limit=limit)


@router.get("/users-with-counts", response_model=List[dict])
async def get_all_users_with_contest_counts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get all users with contest counts using optimized query (admin only)."""
    user_service = UserService(db)
    return await user_service.get_users_with_contest_counts(skip=skip, limit=limit)


@router.patch("/users/{user_id}/credits", response_model=CreditTransactionResponse)
async def update_user_credits(
    user_id: int,
    credit_update: UserCreditUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Update a user's credit balance (admin only)."""
    return await CreditService.add_credits(db, user_id, credit_update)


@router.get("/credits/transactions", response_model=List[CreditTransactionResponse])
async def get_credit_transactions(
    user_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    ai_model: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get filtered credit transactions (admin only)."""
    filters = CreditTransactionFilter(
        user_id=user_id,
        transaction_type=transaction_type,
        ai_model=ai_model,
        date_from=date_from,
        date_to=date_to
    )
    return await CreditService.filter_transactions(db, filters, skip=skip, limit=limit)


@router.get("/credits/transactions-with-users", response_model=List[dict])
async def get_credit_transactions_with_user_info(
    user_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    ai_model: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get filtered credit transactions with user information (admin only)."""
    filters = CreditTransactionFilter(
        user_id=user_id,
        transaction_type=transaction_type,
        ai_model=ai_model,
        date_from=date_from,
        date_to=date_to
    )
    return await CreditService.filter_transactions_with_user_info(db, filters, skip=skip, limit=limit)


@router.get("/credits/summary-stats", response_model=dict)
async def get_filtered_credit_summary_stats(
    user_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    ai_model: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get summary statistics for filtered credit transactions (admin only)."""
    filters = CreditTransactionFilter(
        user_id=user_id,
        transaction_type=transaction_type,
        ai_model=ai_model,
        date_from=date_from,
        date_to=date_to
    )
    return await CreditService.get_filtered_summary_stats(db, filters)


@router.get("/credits/usage", response_model=CreditUsageSummary)
async def get_credit_usage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get a summary of credit usage across the system (admin only)."""
    return await CreditService.get_credit_usage_summary(db) 