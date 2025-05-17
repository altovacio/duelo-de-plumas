from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.db.models.user import User as UserModel
from app.schemas.user import UserResponse
from app.schemas.credit import CreditTransactionResponse
from app.schemas.contest import ContestResponse
from app.services.contest_service import ContestService
from app.services.credit_service import CreditService

router = APIRouter()


@router.get("", response_model=dict)
async def get_user_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's dashboard data."""
    author_contests = await ContestService.get_contests_by_creator(db, current_user.id)
    judge_contests = await ContestService.get_contests_where_user_is_judge(db, current_user.id)

    return {
        "user_info": UserResponse.model_validate(current_user),
        "author_contests": author_contests,
        "judge_contests": judge_contests
    }


@router.get("/credits/transactions", response_model=List[CreditTransactionResponse])
async def get_user_credit_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's credit transaction history."""
    return await CreditService.get_user_transactions(db, current_user.id, skip=skip, limit=limit) 