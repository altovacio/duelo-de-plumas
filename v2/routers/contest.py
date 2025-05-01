from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

# Relative imports from within v2 directory
from .. import schemas, models
from ..database import get_db_session
# from .. import security # Import security later for authentication

router = APIRouter()

# --- Contest CRUD Operations ---

@router.post(
    "/", 
    response_model=schemas.ContestPublic, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contest",
    tags=["Contests"]
)
async def create_contest(
    contest_data: schemas.ContestCreate,
    db: AsyncSession = Depends(get_db_session),
    # current_user: models.User = Depends(security.get_current_active_user) # Add later
):
    """Creates a new contest.
    
    Requires authentication (admin rights likely needed).
    Handles password hashing if contest_type is 'private'.
    """
    # --- Authorization Check (Add later) ---
    # if not current_user.is_admin():
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    # Separate password from other data before creating model instance
    contest_dict = contest_data.model_dump(exclude_unset=True)
    password = contest_dict.pop('password', None) # Remove password from dict, store it

    # Create Contest instance using the rest of the data
    new_contest = models.Contest(**contest_dict)

    # Handle password hashing if private (adapt using passlib later)
    if new_contest.contest_type == 'private' and password:
        # Replace with passlib hashing
        # new_contest.set_password(password) 
        # For now, store plain text (NOT FOR PRODUCTION) or skip password setting
        # Let's skip setting the hash until passlib is integrated
        print(f"Warning: Storing plain password hash placeholder for contest {new_contest.title}") # Add a warning
        new_contest.password_hash = f"hashed_{password}" # Placeholder
        pass # Placeholder for actual hashing
    elif new_contest.contest_type == 'public':
        new_contest.password_hash = None

    db.add(new_contest)
    await db.commit()
    await db.refresh(new_contest) # Refresh to get ID, created_at etc.
    return new_contest

@router.get(
    "/", 
    response_model=List[schemas.ContestPublic], 
    summary="List all contests",
    tags=["Contests"]
)
async def list_contests(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves a list of public contests.
    
    TODO: Filter for private contests based on user access.
    """
    result = await db.execute(
        select(models.Contest)
        .order_by(models.Contest.start_date.desc())
        # .where(models.Contest.contest_type == 'public') # Add filtering later
        .offset(skip)
        .limit(limit)
    )
    contests = result.scalars().all()
    return contests

async def get_contest_or_404(contest_id: int, db: AsyncSession) -> models.Contest:
    """Helper function to get a contest by ID or raise 404, loading relationships."""
    result = await db.execute(
        select(models.Contest)
        .where(models.Contest.id == contest_id)
        .options(
            selectinload(models.Contest.submissions), # Eager load submissions
            selectinload(models.Contest.judges)       # Eager load judges
        )
    )
    contest = result.scalar_one_or_none()
    if contest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    return contest

@router.get(
    "/{contest_id}", 
    response_model=schemas.ContestDetail, 
    summary="Get contest details",
    tags=["Contests"]
)
async def get_contest(
    contest_id: int,
    db: AsyncSession = Depends(get_db_session),
    # current_user: Optional[models.User] = Depends(security.get_current_user_optional) # Add later
):
    """Retrieves detailed information about a specific contest, including submissions and judges.
    
    TODO: Handle access control for private contests.
    """
    contest = await get_contest_or_404(contest_id, db)
    
    # --- Access Control (Add later) ---
    # if contest.contest_type == 'private':
    #     if not current_user or (not current_user.is_admin() and current_user not in contest.judges):
    #         # Check session or password mechanism from Flask app
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Explicitly convert submissions and judges to their Pydantic schemas if needed
    # Pydantic should handle this with from_attributes=True, but manual conversion is possible:
    # contest_detail = schemas.ContestDetail.from_orm(contest)
    # contest_detail.submissions = [schemas.SubmissionPublic.from_orm(sub) for sub in contest.submissions]
    # contest_detail.judges = [schemas.UserPublic.from_orm(judge) for judge in contest.judges]
    # return contest_detail

    return contest # Pydantic will convert using response_model and from_attributes

@router.put(
    "/{contest_id}", 
    response_model=schemas.ContestPublic,
    summary="Update a contest",
    tags=["Contests"]
)
async def update_contest(
    contest_id: int,
    contest_update: schemas.ContestUpdate,
    db: AsyncSession = Depends(get_db_session),
    # current_user: models.User = Depends(security.get_current_admin_user) # Add later
):
    """Updates an existing contest.
    
    Requires admin privileges.
    """
    contest = await get_contest_or_404(contest_id, db) # Fetch existing contest

    # --- Authorization Check (Add later) ---
    # if not current_user.is_admin():
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    update_data = contest_update.model_dump(exclude_unset=True)

    # Handle password update if provided (adapt using passlib later)
    new_password = update_data.pop("password", None)
    if contest.contest_type == 'private' and new_password:
        # Replace with passlib hashing
        # contest.set_password(new_password)
        pass # Placeholder

    # Update contest fields
    for field, value in update_data.items():
        setattr(contest, field, value)

    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest

@router.delete(
    "/{contest_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contest",
    tags=["Contests"]
)
async def delete_contest(
    contest_id: int,
    db: AsyncSession = Depends(get_db_session),
    # current_user: models.User = Depends(security.get_current_admin_user) # Add later
):
    """Deletes a contest and its associated submissions/votes (due to cascade).
    
    Requires admin privileges.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Authorization Check (Add later) ---
    # if not current_user.is_admin():
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    await db.delete(contest)
    await db.commit()
    return None # Return None for 204 status code 