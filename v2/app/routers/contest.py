from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy import or_

# Relative imports from within v2 directory
from ... import schemas, models
from ...database import get_db_session
from ... import security # Corrected: Go up two levels

router = APIRouter()

# --- Contest CRUD Operations ---

@router.post(
    "/",
    response_model=schemas.ContestPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contest (Admin Only)", # Updated summary
    tags=["Contests"]
)
async def create_contest(
    contest_data: schemas.ContestCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.require_admin) # ADDED: Require admin user
):
    """Creates a new contest.

    Requires admin privileges.
    Handles password hashing if contest_type is 'private'.
    """
    # --- Authorization Check is now handled by the dependency --- 

    # Separate password from other data before creating model instance
    contest_dict = contest_data.model_dump(exclude_unset=True)
    password = contest_dict.pop('password', None) # Remove password from dict, store it

    # Create Contest instance using the rest of the data
    new_contest = models.Contest(**contest_dict)

    # Handle password hashing if private
    if new_contest.contest_type == 'private' and password:
        new_contest.set_password(password) # Use the passlib method
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
    db: AsyncSession = Depends(get_db_session),
    # Use the new optional dependency
    current_user: Optional[models.User] = Depends(security.get_optional_current_user)
):
    """Retrieves a list of contests.

    - Public contests are always listed.
    - Private contests are listed only for admins or assigned judges.
    """
    # Base query
    stmt = select(models.Contest).order_by(models.Contest.start_date.desc())
    
    # Filter based on user access for private contests
    if not current_user or not current_user.is_admin():
        # Non-admins or anonymous users see public contests OR private contests they are assigned to
        private_access_filter = models.Contest.judges.any(models.User.id == current_user.id) if current_user else False
        
        stmt = stmt.where(
            or_(
                models.Contest.contest_type == 'public',
                private_access_filter # Only applies if user is logged in
            )
        )
    # Admins see all contests - no additional filtering needed
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
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
    # Use the new optional dependency
    current_user: Optional[models.User] = Depends(security.get_optional_current_user) 
):
    """Retrieves detailed information about a specific contest, including submissions and judges.

    Handles access control for private contests.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Access Control for Private Contests --- 
    if contest.contest_type == 'private':
        is_authorized = False
        if current_user:
            # Allow access if user is an admin
            if current_user.is_admin():
                is_authorized = True
            # Allow access if user is an assigned judge
            # The judges relationship was eager-loaded by get_contest_or_404
            elif current_user in contest.judges:
                is_authorized = True
        
        # TODO: Implement password check mechanism if needed for non-admin/non-judge users
        # Requires a way for the user to provide the password for this request.

        if not is_authorized:
            # If not an admin and not an assigned judge
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: This is a private contest."
            )
    # --- End Access Control --- 

    return contest # Pydantic will convert using response_model and from_attributes

@router.put(
    "/{contest_id}",
    response_model=schemas.ContestPublic,
    summary="Update a contest (Admin Only)", # Updated summary
    tags=["Contests"]
)
async def update_contest(
    contest_id: int,
    contest_update: schemas.ContestUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.require_admin) # ADDED: Require admin user
):
    """Updates an existing contest.

    Requires admin privileges.
    """
    contest = await get_contest_or_404(contest_id, db) # Fetch existing contest

    # --- Authorization Check is now handled by the dependency --- 

    update_data = contest_update.model_dump(exclude_unset=True)

    # Handle password update if provided
    new_password = update_data.pop("password", None)
    if contest.contest_type == 'private' and new_password:
        contest.set_password(new_password) # Use the passlib method
    elif "contest_type" in update_data and update_data["contest_type"] == 'public':
        contest.password_hash = None # Clear hash if changing to public

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
    summary="Delete a contest (Admin Only)", # Updated summary
    tags=["Contests"]
)
async def delete_contest(
    contest_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.require_admin) # ADDED: Require admin user
):
    """Deletes a contest and its associated submissions/votes (due to cascade).

    Requires admin privileges.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Authorization Check is now handled by the dependency --- 

    await db.delete(contest)
    await db.commit()
    return None # Return None for 204 status code 