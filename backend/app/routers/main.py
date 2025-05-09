from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import asyncio

# Correct relative imports for modules two levels up
from ... import schemas, models
from ...database import get_db_session
from ... import security
# Add imports for roadmap
from ..schemas import roadmap_schemas, main_schemas
from ..services import roadmap_service
# Import the new main schema
from ..schemas import main_schemas

from datetime import datetime, timezone # Import datetime tools
from sqlalchemy import select, or_, func # Import select, or_
from sqlalchemy.orm import selectinload

router = APIRouter()

# Add main application endpoints here, e.g., listing submissions, user profiles, etc.

@router.get("/", tags=["Main"])
async def main_root():
    # Placeholder - perhaps redirect to /contests or list recent activity?
    return {"message": "Main application root - functionality TBD"}

# Example: Endpoint to list recent submissions (publicly accessible)
@router.get("/submissions/", response_model=List[schemas.SubmissionPublic], tags=["Main"])
async def list_recent_submissions(
    skip: int = 0,
    limit: int = 20, # Show fewer by default than contest list
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves a list of the most recent submissions across all contests."""
    # TODO: Add filtering to only show submissions from public/accessible contests
    # TODO: Consider performance implications if there are many submissions.
    from sqlalchemy.future import select # Import select locally if not at top level
    
    result = await db.execute(
        select(models.Submission)
        .order_by(models.Submission.submission_date.desc())
        # .where(...) # Add filtering for public contests later
        .offset(skip)
        .limit(limit)
    )
    submissions = result.scalars().all()
    return submissions

# --- Dashboard Endpoint --- 
@router.get(
    "/dashboard-data", 
    response_model=main_schemas.DashboardData,
    tags=["Main"]
)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[models.User] = Depends(security.get_current_user)
):
    """Retrieves aggregated data for the main dashboard/index page."""
    now_aware = datetime.now(timezone.utc)
    
    # --- Base Queries --- 
    # Active Contests (Open, not ended)
    active_contests_stmt = (
        select(models.Contest)
        .where(models.Contest.status == 'open')
        .where(or_(models.Contest.end_date > now_aware, models.Contest.end_date.is_(None)))
        .order_by(models.Contest.end_date.asc())
    )
    
    # Closed Contests
    closed_contests_stmt = (
        select(models.Contest)
        .where(models.Contest.status == 'closed')
        .order_by(models.Contest.end_date.desc())
    )
    
    # --- Conditional Queries (based on user) ---
    judge_eval_stmt = None
    pending_ai_eval_stmt = None
    expired_open_stmt = None
    
    # Data for logged-in judges
    if current_user and current_user.role == 'judge':
        judge_eval_stmt = (
            select(models.Contest)
            .where(models.Contest.status == 'evaluation')
            # Use relationship loading for efficiency if needed, or explicit join
            .where(models.Contest.judges.any(models.User.id == current_user.id))
            .order_by(models.Contest.end_date.asc())
        )
        
    # Data for admins
    if current_user and current_user.is_admin():
        # Expired Open Contests
        expired_open_stmt = (
            select(models.Contest)
            .where(models.Contest.status == 'open')
            .where(models.Contest.end_date.is_not(None))
            .where(models.Contest.end_date <= now_aware)
            .order_by(models.Contest.end_date.asc())
        )
        
        # Contests needing AI Evaluation (more complex query)
        # 1. Find contests in evaluation status
        eval_contests_stmt = (
            select(models.Contest)
            .where(models.Contest.status == 'evaluation')
            .options(selectinload(models.Contest.judges)) # Eager load judges for checking type
            .order_by(models.Contest.end_date.asc())
        )
        eval_contests_result = await db.execute(eval_contests_stmt)
        evaluation_contests = eval_contests_result.scalars().all()
        
        contests_needing_ai_eval_ids = []
        if evaluation_contests:
            # 2. For each evaluation contest, check if AI judges are assigned AND haven't voted
            contest_ids = [c.id for c in evaluation_contests]
            # Get all votes for these contests grouped by judge
            votes_agg_stmt = (
                select(models.Vote.judge_id, func.count(models.Vote.id).label('vote_count'))
                .join(models.Submission)
                .where(models.Submission.contest_id.in_(contest_ids))
                .group_by(models.Vote.judge_id)
            )
            votes_agg_result = await db.execute(votes_agg_stmt)
            judges_with_votes = {row.judge_id for row in votes_agg_result.all()} # Set of judges who voted
            
            for contest in evaluation_contests:
                ai_judges_assigned = [j for j in contest.judges if j.is_ai_judge()]
                if not ai_judges_assigned: continue # Skip if no AI judges
                
                # Check if any assigned AI judge has NOT voted yet
                needs_eval = any(ai_judge.id not in judges_with_votes for ai_judge in ai_judges_assigned)
                if needs_eval:
                    contests_needing_ai_eval_ids.append(contest.id)
            
            if contests_needing_ai_eval_ids:
                 pending_ai_eval_stmt = (
                     select(models.Contest)
                     .where(models.Contest.id.in_(contests_needing_ai_eval_ids))
                     .order_by(models.Contest.end_date.asc())
                 )

    # --- Execute Queries Concurrently (using asyncio.gather) --- 
    # Create dictionary of statements to execute based on conditions
    stmts_to_execute = {
        "active": active_contests_stmt,
        "closed": closed_contests_stmt,
    }
    # Use the original conditions to decide whether to add statements
    if current_user and current_user.role == 'judge':
        # Directly assign the statement if the condition is met
        # No need for inner check: if judge_eval_stmt:
        stmts_to_execute["judge_eval"] = judge_eval_stmt
            
    if current_user and current_user.is_admin():
        # Directly assign the statements if the condition is met
        # No need for inner check: if expired_open_stmt:
        stmts_to_execute["expired"] = expired_open_stmt
        # No need for inner check: if pending_ai_eval_stmt:
        # Check if pending_ai_eval_stmt was actually created (it might be None if no contests needed eval)
        if pending_ai_eval_stmt is not None: 
            stmts_to_execute["pending_ai"] = pending_ai_eval_stmt
    
    # Create execution coroutines
    tasks = {key: db.execute(stmt) for key, stmt in stmts_to_execute.items()}
        
    results = await asyncio.gather(*tasks.values()) # Use asyncio.gather
    results_dict = dict(zip(tasks.keys(), results)) # Map results back to keys
    
    # --- Populate Response Schema --- 
    dashboard_data = main_schemas.DashboardData(
        active_contests=results_dict['active'].scalars().all(),
        closed_contests=results_dict['closed'].scalars().all(),
        judge_assigned_evaluations=results_dict['judge_eval'].scalars().all() if 'judge_eval' in results_dict else None,
        expired_open_contests=results_dict['expired'].scalars().all() if 'expired' in results_dict else None,
        pending_ai_evaluations=results_dict['pending_ai'].scalars().all() if 'pending_ai' in results_dict else None
    )
    
    return dashboard_data

# --- Roadmap API Endpoints --- DELETED

# Add more endpoints as needed based on app/main/routes.py review 