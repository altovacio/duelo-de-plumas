from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from typing import List, Optional
# ADD: AI Client imports for trigger endpoint
import openai
import anthropic
from ..dependencies import get_openai_client, get_anthropic_client
# ADD: AI Service import
from ..services import ai_services

# Correct relative imports for modules two levels up
from ... import schemas, models
from ...database import get_db_session
from ... import security
# ADD: Import AI Schema
from ..schemas.ai_schemas import GenerateTextResponse
import re
import time
from datetime import datetime
# ADD: Import the missing dependency
from ...security import get_current_active_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(security.require_admin)]
)

# --- ADDED: User Management (Focus on Human Judges) ---

@router.get("/users/", response_model=List[schemas.UserPublic], summary="List Users (Filterable)")
async def admin_list_users(
    role: Optional[str] = Query(None, description="Filter by user role (e.g., 'judge')"),
    judge_type: Optional[str] = Query(None, description="Filter by judge type (e.g., 'human')"),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists users, with optional filtering by role and judge type.
    
    Primarily used to list human judges for contest assignment.
    """
    query = select(models.User)
    if role:
        query = query.where(models.User.role == role)
    if judge_type:
        query = query.where(models.User.judge_type == judge_type)
    
    query = query.order_by(models.User.username).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.post("/users/", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED, summary="Create User (Admin Only)")
async def admin_create_user(
    user_in: schemas.UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """(Admin) Creates a new user with a specified role.
    
    Defaults to 'user' role if not provided.
    Sets judge_type to 'human'.
    Requires admin privileges (enforced by router dependency).
    """
    # Verify username and email don't exist
    existing_user = await db.scalar(select(models.User).where(or_(models.User.username == user_in.username, models.User.email == user_in.email)))
    if existing_user:
        field = "Username" if existing_user.username == user_in.username else "Email"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field} already registered."
        )
    
    # Prepare user data, setting defaults if needed
    user_data = user_in.model_dump(exclude={'password'}, exclude_unset=True) # Exclude unset fields
    
    # Set default role if not provided
    if 'role' not in user_data:
        user_data['role'] = 'user'
    
    # Explicitly set judge_type for non-AI judges created here
    user_data['judge_type'] = 'human' 
    
    # Validate the role is allowed (admin or user for this endpoint)
    if user_data['role'] not in ['admin', 'user']:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"Invalid role '{user_data['role']}'. Can only create 'admin' or 'user'."
         )

    new_user = models.User(**user_data)
    new_user.set_password(user_in.password) # Hash the password
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        # This might happen in a race condition if the initial check passes
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or Email already exists (database constraint)."
        )
    except Exception as e:
        await db.rollback()
        print(f"Error creating user: {e}") # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user."
        )

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user (Admin)")
async def delete_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    # current_user: models.User = Depends(require_admin) # Dependency already applied at router level
):
    """Deletes a user by ID. Requires admin privileges.
    
    WARNING: Also deletes all contests created by this user due to creator_id NOT NULL constraint.
    Consider making creator_id nullable and setting to NULL instead if contests should be preserved.
    """
    user_to_delete = await db.get(models.User, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # REMOVED: Manual deletion of User AI Agents - Relying on cascade delete now
    # print(f"---> Deleting AI Agents owned by user {user_id}...")
    # # Delete UserAIWriters
    # writer_delete_stmt = delete(models.UserAIWriter).where(models.UserAIWriter.owner_id == user_id)
    # await db.execute(writer_delete_stmt)
    # # Delete UserAIJudges
    # judge_delete_stmt = delete(models.UserAIJudge).where(models.UserAIJudge.owner_id == user_id)
    # await db.execute(judge_delete_stmt)
    # # Ensure agent deletions are flushed before proceeding
    # await db.flush()
    # print(f"---> Flushed deletion of AI Agents for user {user_id}")

    # Find and delete contests created by this user
    contests_to_delete = await db.scalars(
        select(models.Contest).where(models.Contest.creator_id == user_id)
    )
    deleted_contest_count = 0
    for contest in contests_to_delete.all():
        print(f"---> Deleting contest {contest.id} (created by user {user_id}) before deleting user.") # DEBUG
        await db.delete(contest) # Deleting contest will cascade to its submissions/votes etc.
        deleted_contest_count += 1
    
    if deleted_contest_count > 0:
        # Flush the contest deletions before deleting the user
        print(f"---> Flushing deletion of {deleted_contest_count} contests created by user {user_id}") # DEBUG
        await db.flush() 

    print(f"---> Deleting user {user_id}") # DEBUG
    await db.delete(user_to_delete) # This should now succeed
    print(f"---> Committing transaction for user {user_id} deletion") # DEBUG
    await db.commit()
    print(f"---> Commit successful for user {user_id} deletion") # DEBUG
    return None # FastAPI handles 204 No Content automatically

# ADDED: Endpoint for updating user credits
@router.put("/users/{user_id}/credits", response_model=schemas.UserPublic, summary="Update User Credits (Admin)")
async def admin_update_user_credits(
    user_id: int,
    credit_update: schemas.AdminUserCreditUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin: models.User = Depends(security.require_admin) # Ensure we get the admin performing the action
):
    """(Admin) Sets or adjusts the credit balance for a specific user and logs the transaction.
    
    Requires admin privileges.
    Uses AdminUserCreditUpdate schema which allows either setting an absolute value (`credits`)
    or adding/subtracting (`add_credits`).
    Logs the change in the CostLedger.
    """
    # Use select for update to lock the user row during the transaction
    result = await db.execute(
        select(models.User).where(models.User.id == user_id).with_for_update()
    )
    user_to_update = result.scalar_one_or_none()

    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with id {user_id} not found"
        )

    # Determine the change and the new balance
    original_balance = user_to_update.credits
    credits_change = 0
    description_detail = ""

    if credit_update.credits is not None: # Set absolute value
        new_balance = credit_update.credits
        credits_change = new_balance - original_balance
        description_detail = f"set credits to {new_balance}"
    elif credit_update.add_credits is not None: # Add/subtract value
        credits_change = credit_update.add_credits
        new_balance = original_balance + credits_change
        if new_balance < 0:
            # Prevent negative balance through adjustments unless explicitly allowed?
            # For now, let's allow it as admin might need to zero out or fix issues.
            pass # Or raise HTTPException(status_code=400, detail="Adjustment results in negative balance")
        op_type = "added" if credits_change > 0 else "subtracted"
        description_detail = f"{op_type} {abs(credits_change)} credits"
    else:
        # This case should be prevented by the schema validator, but handle defensively
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request: Must provide either 'credits' or 'add_credits'"
        )

    # Update user credits
    user_to_update.credits = new_balance

    # Create CostLedger entry
    ledger_entry = models.CostLedger(
        user_id=user_to_update.id,
        action_type='admin_credit_adjust',
        credits_change=credits_change,
        real_cost=None, # No real cost associated with admin adjustments
        description=f"Admin '{current_admin.username}' {description_detail}. Original balance: {original_balance}.",
        related_entity_type='user', # The entity acted upon is the user itself
        related_entity_id=current_admin.id, # Could store the admin ID here for tracking
        resulting_balance=new_balance
    )

    db.add(user_to_update)
    db.add(ledger_entry)

    try:
        await db.commit()
        await db.refresh(user_to_update)
        # Optionally refresh ledger_entry if its ID is needed later
        # await db.refresh(ledger_entry)
        return user_to_update
    except Exception as e:
        await db.rollback()
        # Log the error
        print(f"Error updating user credits for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user credits and log transaction."
        )

# ADDED: Endpoint for retrieving user credit history
@router.get("/users/{user_id}/credit-history", response_model=List[schemas.CostLedgerRead], summary="Get User Credit History (Admin)")
async def admin_get_user_credit_history(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """(Admin) Retrieves the credit transaction history for a specific user from the CostLedger.
    
    Requires admin privileges.
    Results are ordered by timestamp descending.
    """
    # Check if user exists (optional, but good practice)
    user_exists = await db.get(models.User, user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"User with id {user_id} not found"
        )
        
    stmt = (
        select(models.CostLedger)
        .where(models.CostLedger.user_id == user_id)
        .order_by(models.CostLedger.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    ledger_entries = result.scalars().all()
    return ledger_entries

# --- AI Writer Management ---

@router.get("/ai-writers", response_model=List[schemas.AIWriterAdminView])
async def admin_list_ai_writers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all configured AI Writers."""
    result = await db.execute(
        select(models.AIWriter)
        .order_by(models.AIWriter.name)
        .offset(skip)
        .limit(limit)
    )
    writers = result.scalars().all()
    return writers

@router.post("/ai-writers", response_model=schemas.AIWriterAdminView, status_code=status.HTTP_201_CREATED)
async def admin_create_ai_writer(
    writer_data: schemas.AIWriterCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new AI Writer."""
    existing_writer = await db.scalar(select(models.AIWriter).where(models.AIWriter.name == writer_data.name))
    if existing_writer:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Writer with name '{writer_data.name}' already exists.")
    new_writer = models.AIWriter(**writer_data.model_dump())
    db.add(new_writer)
    await db.commit()
    await db.refresh(new_writer)
    return new_writer

@router.get("/ai-writers/{writer_id}", response_model=schemas.AIWriterAdminView)
async def admin_get_ai_writer(
    writer_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets details of a specific AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    return writer

@router.put("/ai-writers/{writer_id}", response_model=schemas.AIWriterAdminView)
async def admin_update_ai_writer(
    writer_id: int,
    writer_update: schemas.AIWriterUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Updates an existing AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    update_data = writer_update.model_dump(exclude_unset=True)
    if 'name' in update_data and update_data['name'] != writer.name:
        existing_writer = await db.scalar(select(models.AIWriter).where(models.AIWriter.name == update_data['name']))
        if existing_writer:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Writer with name '{update_data['name']}' already exists.")
    for field, value in update_data.items():
        setattr(writer, field, value)
    db.add(writer)
    await db.commit()
    await db.refresh(writer)
    return writer

@router.delete("/ai-writers/{writer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_ai_writer(
    writer_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes an AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    await db.delete(writer)
    await db.commit()
    return None

# --- Contest Status/Password Management ---

@router.put("/contests/{contest_id}/status", response_model=schemas.ContestPublic, summary="Set Contest Status")
async def admin_set_contest_status(
    contest_id: int,
    status_data: schemas.ContestSetStatusRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Manually sets the status of a contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    contest.status = status_data.status
    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest

@router.put("/contests/{contest_id}/reset-password", status_code=status.HTTP_200_OK, summary="Reset Private Contest Password")
async def admin_reset_contest_password(
    contest_id: int,
    password_data: schemas.ContestResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Sets a new password for a private contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.contest_type != 'private':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot set password for a public contest.")
    contest.set_password(password_data.new_password)
    db.add(contest)
    await db.commit()
    return {"message": "Contest password reset successfully"}

# --- AI Judge Management (Dedicated Model) ---

@router.get("/ai-judges", response_model=List[schemas.AIJudgeRead])
async def admin_list_ai_judges(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all configured AI Judges."""
    result = await db.execute(
        select(models.AIJudge)
        .order_by(models.AIJudge.name)
        .offset(skip)
        .limit(limit)
    )
    ai_judges = result.scalars().all()
    return ai_judges

@router.post("/ai-judges", response_model=schemas.AIJudgeRead, status_code=status.HTTP_201_CREATED)
async def admin_create_ai_judge(
    judge_data: schemas.AIJudgeCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new AI Judge configuration."""
    existing_judge = await db.scalar(select(models.AIJudge).where(models.AIJudge.name == judge_data.name))
    if existing_judge:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Judge with name '{judge_data.name}' already exists.")
    
    new_judge = models.AIJudge(**judge_data.model_dump())
    db.add(new_judge)
    await db.commit()
    await db.refresh(new_judge)
    return new_judge

@router.get("/ai-judges/{ai_judge_id}", response_model=schemas.AIJudgeRead)
async def admin_get_ai_judge(
    ai_judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets details of a specific AI Judge configuration."""
    judge = await db.get(models.AIJudge, ai_judge_id)
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    return judge

@router.put("/ai-judges/{ai_judge_id}", response_model=schemas.AIJudgeRead)
async def admin_update_ai_judge(
    ai_judge_id: int,
    judge_update: schemas.AIJudgeUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Updates an existing AI Judge configuration."""
    judge = await db.get(models.AIJudge, ai_judge_id)
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    
    update_data = judge_update.model_dump(exclude_unset=True)
    
    if 'name' in update_data and update_data['name'] != judge.name:
        existing = await db.scalar(select(models.AIJudge).where(models.AIJudge.name == update_data['name']))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Judge name '{update_data['name']}' already exists")

    for field, value in update_data.items():
        setattr(judge, field, value)
        
    judge.updated_at = datetime.utcnow() # Manually update timestamp
    db.add(judge)
    await db.commit()
    await db.refresh(judge)
    return judge

@router.delete("/ai-judges/{ai_judge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_ai_judge(
    ai_judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes an AI Judge configuration."""
    judge = await db.get(models.AIJudge, ai_judge_id)
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    
    # Check assignments before deleting
    assigned_contests = await db.scalar(select(func.count(models.contest_ai_judges.c.contest_id)).where(models.contest_ai_judges.c.ai_judge_id == ai_judge_id))
    if assigned_contests > 0:
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete AI Judge {judge.name} as it is assigned to {assigned_contests} contest(s). Remove assignments first.")

    await db.delete(judge)
    await db.commit()
    return None

# --- Renamed Human Judge Assignment --- 
@router.post("/contests/{contest_id}/human-judges/{user_id}", status_code=status.HTTP_201_CREATED, summary="Assign Human Judge to Contest")
async def admin_assign_human_judge_to_contest(
    contest_id: int,
    user_id: int,
    assignment_data: schemas.AssignHumanJudgeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user)
):
    """Assigns a human judge (User) to a specific contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    judge = await db.get(models.User, user_id)
    if not judge or judge.role != 'judge' or judge.judge_type != 'human':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Human judge user not found")

    existing_assignment = await db.execute(
        select(models.contest_human_judges.c.user_id)
        .where(models.contest_human_judges.c.contest_id == contest_id)
        .where(models.contest_human_judges.c.user_id == user_id)
    )
    if existing_assignment.first():
        return {"message": f"Human Judge {judge.username} already assigned to contest {contest.title}"}

    try:
        insert_stmt = models.contest_human_judges.insert().values(
            contest_id=contest_id,
            user_id=user_id,
            ai_model=None # Explicitly None for human judges
        )
        await db.execute(insert_stmt)
        await db.commit()
        return {"message": f"Human Judge {judge.username} assigned to contest {contest.title}"} 
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assign human judge: {e}")

@router.delete("/contests/{contest_id}/human-judges/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unassign Human Judge from Contest")
async def admin_unassign_human_judge_from_contest(
    contest_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Removes a human judge assignment from a contest."""
    # Verify assignment exists
    existing_assignment = await db.execute(
        select(models.contest_human_judges.c.user_id)
        .where(models.contest_human_judges.c.contest_id == contest_id)
        .where(models.contest_human_judges.c.user_id == user_id)
    )
    if not existing_assignment.first():
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Human judge assignment not found for this contest")
    
    # TODO: Check if judge has submitted votes before allowing unassignment?

    try:
        delete_stmt = models.contest_human_judges.delete().where(
            models.contest_human_judges.c.contest_id == contest_id,
            models.contest_human_judges.c.user_id == user_id
        )
        await db.execute(delete_stmt)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unassign human judge: {e}")

# --- NEW AI Judge Assignment --- 
@router.post("/contests/{contest_id}/ai-judges/{ai_judge_id}", status_code=status.HTTP_201_CREATED, summary="Assign AI Judge to Contest")
async def admin_assign_ai_judge_to_contest(
    contest_id: int,
    ai_judge_id: int,
    assignment_data: schemas.AssignAIJudgeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Assigns an AI judge configuration to a specific contest with a specified model."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    ai_judge = await db.get(models.AIJudge, ai_judge_id)
    if not ai_judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge configuration not found")
    
    # TODO: Validate assignment_data.ai_model against available models?

    existing_assignment = await db.execute(
        select(models.contest_ai_judges)
        .where(models.contest_ai_judges.c.contest_id == contest_id)
        .where(models.contest_ai_judges.c.ai_judge_id == ai_judge_id)
    )
    assignment_row = existing_assignment.first()

    if assignment_row:
        # If assignment exists, update the model if it's different
        if assignment_row.ai_model != assignment_data.ai_model:
            stmt = (
                models.contest_ai_judges.update()
                .where(models.contest_ai_judges.c.contest_id == contest_id)
                .where(models.contest_ai_judges.c.ai_judge_id == ai_judge_id)
                .values(ai_model=assignment_data.ai_model)
            )
            await db.execute(stmt)
            await db.commit()
            return {"message": f"AI Judge {ai_judge.name} model updated to {assignment_data.ai_model} for contest {contest.title}"}
        else:
            return {"message": f"AI Judge {ai_judge.name} already assigned to contest {contest.title} with model {assignment_data.ai_model}"}
    else:
        # Create new assignment
        try:
            insert_stmt = models.contest_ai_judges.insert().values(
                contest_id=contest_id,
                ai_judge_id=ai_judge_id,
                ai_model=assignment_data.ai_model
            )
            await db.execute(insert_stmt)
            await db.commit()
            return {"message": f"AI Judge {ai_judge.name} assigned to contest {contest.title} with model {assignment_data.ai_model}"} 
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assign AI judge: {e}")

@router.delete("/contests/{contest_id}/ai-judges/{ai_judge_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unassign AI Judge from Contest")
async def admin_unassign_ai_judge_from_contest(
    contest_id: int,
    ai_judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Removes an AI judge assignment from a contest."""
    # Verify assignment exists
    existing_assignment = await db.execute(
        select(models.contest_ai_judges.c.ai_judge_id)
        .where(models.contest_ai_judges.c.contest_id == contest_id)
        .where(models.contest_ai_judges.c.ai_judge_id == ai_judge_id)
    )
    if not existing_assignment.first():
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI judge assignment not found for this contest")

    # TODO: Check if AI judge has submitted evaluations before allowing unassignment?

    try:
        delete_stmt = models.contest_ai_judges.delete().where(
            models.contest_ai_judges.c.contest_id == contest_id,
            models.contest_ai_judges.c.ai_judge_id == ai_judge_id
        )
        await db.execute(delete_stmt)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unassign AI judge: {e}")

# --- AI Evaluation Info ---

@router.get("/ai-evaluations", response_model=List[schemas.AIEvaluationPublic], summary="List AI Evaluations")
async def admin_list_ai_evaluations(
    contest_id: Optional[int] = None,
    judge_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists AI evaluation records, optionally filtered."""
    stmt = select(models.AIEvaluation).order_by(models.AIEvaluation.timestamp.desc())
    if contest_id:
        stmt = stmt.where(models.AIEvaluation.contest_id == contest_id)
    if judge_id:
        stmt = stmt.where(models.AIEvaluation.judge_id == judge_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    evaluations = result.scalars().all()
    return evaluations

@router.get("/ai-evaluations/{evaluation_id}", response_model=schemas.AIEvaluationDetail, summary="Get AI Evaluation Details")
async def admin_get_ai_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets the full details of a specific AI evaluation record."""
    evaluation = await db.get(models.AIEvaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Evaluation record not found")
    return evaluation

# --- ADDED: AI Cost Summary --- 

@router.get("/ai-costs-summary", response_model=schemas.AICostsSummary, summary="Get AI Costs Summary")
async def admin_get_ai_costs_summary(
    recent_limit: int = Query(10, description="Number of recent evaluations/requests to return"),
    db: AsyncSession = Depends(get_db_session)
):
    """Calculates and returns a summary of AI API costs and token usage.
    
    Uses CostLedger for cost aggregation and AIEvaluation/AIWritingRequest for token counts and recent records.
    """
    summary = schemas.AICostsSummary()
    
    # --- Aggregate Costs from CostLedger --- 
    eval_cost_stmt = select(func.sum(models.CostLedger.real_cost)).where(
        models.CostLedger.action_type == 'ai_evaluate',
        models.CostLedger.real_cost.isnot(None)
    )
    eval_cost_result = (await db.execute(eval_cost_stmt)).scalar_one_or_none() or 0.0
    summary.evaluation_cost = eval_cost_result

    write_cost_stmt = select(func.sum(models.CostLedger.real_cost)).where(
        models.CostLedger.action_type == 'ai_generate',
        models.CostLedger.real_cost.isnot(None)
    )
    write_cost_result = (await db.execute(write_cost_stmt)).scalar_one_or_none() or 0.0
    summary.writing_cost = write_cost_result

    summary.total_cost = summary.evaluation_cost + summary.writing_cost

    # --- Aggregate Token Counts from Original Tables (If needed) --- 
    eval_token_stmt = select(
        func.sum(models.AIEvaluation.prompt_tokens).label("total_prompt"),
        func.sum(models.AIEvaluation.completion_tokens).label("total_completion")
    )
    eval_token_result = (await db.execute(eval_token_stmt)).first()
    if eval_token_result:
        summary.evaluation_prompt_tokens = eval_token_result.total_prompt or 0
        summary.evaluation_completion_tokens = eval_token_result.total_completion or 0
        summary.total_prompt_tokens += summary.evaluation_prompt_tokens
        summary.total_completion_tokens += summary.evaluation_completion_tokens

    write_token_stmt = select(
        func.sum(models.AIWritingRequest.prompt_tokens).label("total_prompt"),
        func.sum(models.AIWritingRequest.completion_tokens).label("total_completion")
    )
    write_token_result = (await db.execute(write_token_stmt)).first()
    if write_token_result:
        summary.writing_prompt_tokens = write_token_result.total_prompt or 0
        summary.writing_completion_tokens = write_token_result.total_completion or 0
        summary.total_prompt_tokens += summary.writing_prompt_tokens
        summary.total_completion_tokens += summary.writing_completion_tokens
        
    # --- Aggregate Costs by Model (Requires joining or separate queries) --- 
    # Option 1: Query CostLedger and group by description/related_entity? (Might be complex)
    # Option 2: Keep querying original tables for model-specific cost/tokens (Simpler for now)
    model_costs = {}
    eval_model_stmt = select(
        models.AIEvaluation.ai_model,
        func.sum(models.AIEvaluation.cost).label("cost"), # Using AIEvaluation.cost here as CostLedger doesn't store model easily
        func.sum(models.AIEvaluation.prompt_tokens).label("prompt"),
        func.sum(models.AIEvaluation.completion_tokens).label("completion")
    ).group_by(models.AIEvaluation.ai_model)
    eval_model_results = (await db.execute(eval_model_stmt)).all()
    for row in eval_model_results:
        if row.ai_model not in model_costs:
            model_costs[row.ai_model] = {"cost": 0.0, "prompt": 0, "completion": 0}
        model_costs[row.ai_model]["cost"] += row.cost or 0.0
        model_costs[row.ai_model]["prompt"] += row.prompt or 0
        model_costs[row.ai_model]["completion"] += row.completion or 0

    write_model_stmt = select(
        models.AIWritingRequest.ai_model,
        func.sum(models.AIWritingRequest.cost).label("cost"), # Using AIWritingRequest.cost here
        func.sum(models.AIWritingRequest.prompt_tokens).label("prompt"),
        func.sum(models.AIWritingRequest.completion_tokens).label("completion")
    ).group_by(models.AIWritingRequest.ai_model)
    write_model_results = (await db.execute(write_model_stmt)).all()
    for row in write_model_results:
        if row.ai_model not in model_costs:
            model_costs[row.ai_model] = {"cost": 0.0, "prompt": 0, "completion": 0}
        # Ensure cost is float, tokens are int, handling None
        cost_val = float(row.cost) if row.cost is not None else 0.0
        prompt_val = int(row.prompt) if row.prompt is not None else 0
        completion_val = int(row.completion) if row.completion is not None else 0
        
        model_costs[row.ai_model]["cost"] += cost_val
        model_costs[row.ai_model]["prompt"] += prompt_val
        model_costs[row.ai_model]["completion"] += completion_val

    summary.cost_by_model = [
        schemas.ModelCostSummary(model_name=k, **v) for k, v in model_costs.items()
    ]

    # --- Fetch Recent Records (Keep using original tables for AIEvaluationPublic/AIWritingRequestPublic) --- 
    if recent_limit > 0:
        recent_eval_stmt = select(models.AIEvaluation).order_by(models.AIEvaluation.timestamp.desc()).limit(recent_limit)
        summary.recent_evaluations = (await db.scalars(recent_eval_stmt)).all()
        
        recent_write_stmt = select(models.AIWritingRequest).order_by(models.AIWritingRequest.timestamp.desc()).limit(recent_limit)
        summary.recent_writing_requests = (await db.scalars(recent_write_stmt)).all()

    return summary

# --- AI Writer Submission Trigger ---

@router.post("/contests/{contest_id}/ai-submission", response_model=GenerateTextResponse, summary="Trigger AI Submission")
async def admin_trigger_ai_submission(
    contest_id: int,
    submission_request: schemas.TriggerAISubmissionRequest,
    db: AsyncSession = Depends(get_db_session),
    openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client),
    anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
):
    """Triggers an AI Writer to generate and submit text for a contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.status != 'open':
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contest status is '{contest.status}', must be 'open' to submit.")
    result = await ai_services.generate_text(
        session=db,
        contest_id=contest_id,
        ai_writer_id=submission_request.ai_writer_id,
        model_id=submission_request.model_id,
        title=submission_request.title,
        openai_client=openai_client,
        anthropic_client=anthropic_client
    )
    if not result.get("success"): 
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = result.get("message", "Failed to generate AI submission.")
        if "not found" in detail.lower(): status_code = status.HTTP_404_NOT_FOUND
        elif "not open" in detail.lower(): status_code = status.HTTP_400_BAD_REQUEST
        elif "error calling ai api" in detail.lower(): status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=status_code, detail=detail)
    return result

# --- Submission Management (Ensure correct placement) ---

@router.delete("/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Submission")
async def admin_delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes a specific submission and its associated votes (due to cascade)."""
    submission = await db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    await db.delete(submission)
    await db.commit()
    return None

# --- ADDED: Trigger AI Evaluation --- 

@router.post("/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate", response_model=schemas.AIEvaluationDetail, summary="Trigger AI Judge Evaluation")
async def admin_trigger_ai_evaluation(
    contest_id: int,
    ai_judge_id: int, # From path
    session: AsyncSession = Depends(get_db_session),
    openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client),
    anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client),
    current_user: models.User = Depends(get_current_active_user) # Admin check done by router dependency
) -> schemas.AIEvaluationDetail:
    """
    Triggers AI evaluation for a specific contest using a designated AI judge configuration.
    Requires admin privileges.
    """
    # The user authentication (require_admin) is handled by the main router dependency
    try:
        result = await ai_services.run_ai_evaluation(
            contest_id=contest_id,
            ai_judge_id=ai_judge_id, # Pass AI Judge config ID from path
            admin_user_id=current_user.id, # Pass triggering admin user ID
            session=session,
            openai_client=openai_client,
            anthropic_client=anthropic_client,
        )
        
        if not result.get("success"):
             status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
             detail = result.get("message", "AI evaluation failed.")
             if "not found" in detail.lower():
                 status_code = status.HTTP_404_NOT_FOUND
             elif "invalid state" in detail.lower():
                 status_code = status.HTTP_409_CONFLICT
             # Add specific check for assignment error from service
             elif "not assigned" in detail.lower():
                 status_code = status.HTTP_400_BAD_REQUEST 
             raise HTTPException(status_code=status_code, detail=detail)
            
        # Ensure the returned dict matches the AIEvaluationResult schema fields
        # The service function might return extra keys ('cost', 'votes_created', etc.)
        # Filter the result dict or ensure AIEvaluationResult allows extra fields if needed.
        # Assuming AIEvaluationResult is defined correctly to handle the output of run_ai_evaluation.
        return schemas.AIEvaluationDetail(**result)
    
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        print(f"Error during AI evaluation trigger: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during AI evaluation trigger."
        )

# --- Other Admin Endpoints (Placeholders) ---
# TODO: Implement endpoints for:
# - Listing/Managing Users (Human Judges, Admins)
# - Overriding Contest status/passwords (Partially done)
# - Viewing detailed AI evaluation costs/logs (Partially done)
# - Triggering AI submissions for contests (Done)
