from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.auth import get_current_admin_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.credit import UserCreditUpdate, CreditTransactionResponse, CreditUsageSummary, CreditTransactionFilter
from app.services.user_service import UserService
from app.services.credit_service import CreditService
from app.db.models.user import User as UserModel

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get all users (admin only)."""
    return UserService.get_all_users(db, skip, limit)


@router.patch("/users/{user_id}/credits", response_model=CreditTransactionResponse)
def update_user_credits(
    user_id: int,
    credit_update: UserCreditUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Update a user's credit balance (admin only)."""
    return CreditService.add_credits(db, user_id, credit_update)


@router.get("/credits/transactions", response_model=List[CreditTransactionResponse])
def get_credit_transactions(
    user_id: int = None,
    transaction_type: str = None,
    ai_model: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get filtered credit transactions (admin only)."""
    filters = CreditTransactionFilter(
        user_id=user_id,
        transaction_type=transaction_type,
        ai_model=ai_model
    )
    return CreditService.filter_transactions(db, filters, skip, limit)


@router.get("/credits/usage", response_model=CreditUsageSummary)
def get_credit_usage_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin_user)
):
    """Get a summary of credit usage across the system (admin only)."""
    return CreditService.get_credit_usage_summary(db) 