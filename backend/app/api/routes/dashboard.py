from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.db.models.user import User as UserModel
from app.schemas.user import UserResponse
from app.schemas.credit import CreditTransactionResponse
from app.schemas.contest import ContestResponse
from app.services.contest_service import ContestService
from app.services.credit_service import CreditService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=dict)
def get_user_dashboard(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's dashboard data."""
    # Get contests where the user is an author
    author_contests = ContestService.get_contests_by_author(db, current_user.id)
    
    # Get contests where the user is a judge
    judge_contests = ContestService.get_contests_by_judge(db, current_user.id)
    
    return {
        "credits": current_user.credits,
        "author_contests": author_contests,
        "judge_contests": judge_contests
    }


@router.get("/credits/transactions", response_model=List[CreditTransactionResponse])
def get_user_credit_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's credit transaction history."""
    return CreditService.get_user_transactions(db, current_user.id, skip, limit) 