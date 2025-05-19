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
from app.services.text_service import TextService
from app.services.agent_service import AgentService
from app.db.repositories.vote_repository import VoteRepository

router = APIRouter()


@router.get("", response_model=dict)
async def get_user_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's dashboard data."""
    author_contests = await ContestService.get_contests_by_creator(db, current_user.id)
    judge_contests = await ContestService.get_contests_where_user_is_judge(db, current_user.id)
    
    text_service = TextService(db)
    user_texts = await text_service.get_user_texts(current_user.id)
    
    user_agents = await AgentService.get_agents_by_owner(db, current_user.id)
    
    urgent_actions = []
    for contest in judge_contests:
        if contest.status.lower() == "evaluation":
            judge_entries = await ContestService.get_contest_judges(db, contest.id, current_user.id)
            
            user_judge_entry = next((j for j in judge_entries if j.user_judge_id == current_user.id), None)
            
            if user_judge_entry and not user_judge_entry.has_voted:
                urgent_actions.append({
                    "type": "judge_contest",
                    "contest_id": contest.id,
                    "contest_title": contest.title,
                })
    
    dashboard_data = {
        "user_info": UserResponse.model_validate(current_user),
        "author_contests": author_contests,
        "judge_contests": judge_contests,
        "credit_balance": current_user.credits,
        "urgent_actions": urgent_actions,
        "contest_count": len(author_contests),
        "text_count": len(user_texts),
        "agent_count": len(user_agents),
        "participation": {
            "as_author": len(author_contests),
            "as_judge": len(judge_contests)
        }
    }
    
    return dashboard_data


@router.get("/credits/transactions", response_model=List[CreditTransactionResponse])
async def get_user_credit_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get the current user's credit transaction history."""
    return await CreditService.get_user_transactions(db, current_user.id, skip=skip, limit=limit) 