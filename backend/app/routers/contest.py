from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy import or_, delete
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

# Relative imports
from ... import models, schemas
from ...database import get_db_session
from ...security import get_current_active_user, get_optional_current_user, require_admin, create_access_token
from ...fastapi_config import settings

router = APIRouter(
    prefix="/contests",
    tags=["Contests"], 
    # dependencies=[Depends(get_current_active_user)], # Apply auth to all routes in this router if needed
    responses={404: {"description": "Not found"}},
)

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
    current_user: models.User = Depends(require_admin) # Use imported function directly
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
    status: Optional[str] = Query(None, description="Filter by contest status (open, evaluation, closed)"),
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[models.User] = Depends(get_optional_current_user) # Use imported function directly
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
    
    if status:
        stmt = stmt.where(models.Contest.status == status)
    
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
    current_user: Optional[models.User] = Depends(get_optional_current_user) # Use imported function directly
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
    current_user: models.User = Depends(require_admin) # Use imported function directly
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
    current_user: models.User = Depends(require_admin) # Use imported function directly
):
    """Deletes a contest and its associated submissions/votes (due to cascade).

    Requires admin privileges.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Authorization Check is now handled by the dependency --- 

    await db.delete(contest)
    await db.commit()
    return None # Return None for 204 status code 

# --- Submit to Contest ---

@router.post("/{contest_id}/submissions", response_model=schemas.SubmissionRead, status_code=status.HTTP_201_CREATED, summary="Submit an Entry to a Contest")
async def create_submission(
    contest_id: int,
    submission_data: schemas.SubmissionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[models.User] = Depends(get_optional_current_user) # Correct dependency for optional user
):
    """Creates a new submission for an open contest."""
    # 1. Get Contest and check status
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.status != 'open':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contest is not open for submissions")

    # 2. Prepare submission data
    submission_dict = submission_data.model_dump()
    
    author_name = submission_dict.get('author_name')
    if not author_name and current_user:
        author_name = current_user.username
    elif not author_name:
        author_name = "Anonymous"
        
    submission_dict['author_name'] = author_name
    submission_dict['contest_id'] = contest_id
    submission_dict['submission_date'] = datetime.utcnow()
    submission_dict['is_ai_generated'] = False
    submission_dict['ai_writer_id'] = None
    submission_dict['user_id'] = current_user.id if current_user else None
    word_count = len(submission_dict.get('text_content', '').split())
    # Note: word_count is calculated but Submission model doesn't have this field.
    # We can add it later if needed, or just return it in the schema.

    # 3. Create Submission
    try:
        # Prepare data strictly for the model
        model_data = {
            "title": submission_dict["title"],
            "text_content": submission_dict["text_content"],
            "author_name": submission_dict["author_name"],
            "contest_id": submission_dict["contest_id"],
            "submission_date": submission_dict["submission_date"],
            "is_ai_generated": submission_dict["is_ai_generated"],
            "ai_writer_id": submission_dict["ai_writer_id"],
            "user_id": submission_dict["user_id"]
            # Ensure no fields like 'word_count' are passed if not in model
        }
        new_submission = models.Submission(**model_data)
        db.add(new_submission)
        await db.commit()
        await db.refresh(new_submission)
        
        # Prepare response using SubmissionRead schema
        response_data = schemas.SubmissionRead(
            id=new_submission.id,
            title=new_submission.title,
            text_content=new_submission.text_content, 
            author_name=new_submission.author_name,
            contest_id=new_submission.contest_id,
            user_id=new_submission.user_id,
            timestamp=new_submission.submission_date, # Use submission_date from model for timestamp
            word_count=word_count, # Include calculated word_count in response schema
            votes=[] # Votes list is empty initially
        )
        return response_data
        
    except IntegrityError as e:
        await db.rollback()
        # Log specific IntegrityError if helpful
        print(f"IntegrityError creating submission: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database integrity error. Ensure data is valid.")
    except Exception as e:
        await db.rollback()
        print(f"Unexpected error creating submission: {e}") # Log the error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create submission")

# --- Get Submissions for a Contest (Judge/Admin Access) ---
@router.get("/{contest_id}/submissions", response_model=List[schemas.SubmissionRead])
async def get_contest_submissions(
    contest_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Use imported function directly
):
    """Get all submissions for a specific contest (Requires judge/admin access)."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    # Authorization Check: Only admin or assigned judges can view submissions
    is_admin = current_user.role == 'admin'
    # Check if user is an assigned human judge
    is_assigned_human = any(assign.user_id == current_user.id for assign in contest.human_judge_assignments)
    # Check if user is an assigned AI judge (less likely scenario for this specific check, but possible)
    # Assuming AI Judge functionality links back to a User with role 'judge' and type 'ai'
    # This requires loading the AIJudge configurations linked to the user
    # Simpler check: Is user a judge assigned to this contest?
    is_judge_assigned = is_assigned_human # Add AI judge assignment check if needed
    
    if not is_admin and not is_judge_assigned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view submissions for this contest")

    # Fetch submissions
    result = await db.execute(
        select(models.Submission)
        .where(models.Submission.contest_id == contest_id)
        .order_by(models.Submission.submission_date) # Or order by ID?
    )
    submissions = result.scalars().all()
    return submissions

# --- Contest Password Check Endpoint ---
@router.post("/{contest_id}/check-password", status_code=status.HTTP_200_OK)
async def check_contest_password(
    contest_id: int,
    password_data: schemas.ContestCheckPasswordRequest, # Define this schema
    response: Response, # Inject response object to set cookies
    db: AsyncSession = Depends(get_db_session)
):
    """Checks if the provided password is correct for a private contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.contest_type != 'private':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contest is not private")

    if not contest.check_password(password_data.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password")

    # Password is correct. Set a temporary access cookie.
    # The cookie value should be a signed token containing contest_id and expiry.
    # Use settings for secret key and cookie name/duration.
    # This is a simplified example:
    access_token = create_access_token(
        data={"sub": f"contest_access:{contest_id}", "contest_id": contest_id},
        expires_delta=timedelta(minutes=settings.CONTEST_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(
        key=f"contest_access_{contest_id}", 
        value=access_token,
        max_age=settings.CONTEST_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True, # Important for security
        samesite="lax", # Or "strict"
        # secure=True, # Set to True in production with HTTPS
    )
    
    return {"message": "Password accepted"}

# --- Submit Judge Evaluation --- 
@router.post("/{contest_id}/evaluate", status_code=status.HTTP_200_OK, summary="Submit Judge Evaluation for a Contest")
async def submit_evaluation(
    contest_id: int,
    evaluation_data: List[schemas.VoteCreate],
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Requires authenticated user
):
    """Allows an assigned judge to submit their evaluation (votes/rankings) for a contest."""
    # 1. Verify contest exists and is in evaluation status
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.status != 'evaluation':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contest status is '{contest.status}', must be 'evaluation' to submit votes.")

    # 2. Verify user is an assigned HUMAN judge for this contest
    # TODO: Add check for AI judge role if they can submit votes this way?
    is_assigned_human_judge = await db.scalar(
        select(models.ContestHumanJudgeAssociation)
        .where(models.ContestHumanJudgeAssociation.contest_id == contest_id)
        .where(models.ContestHumanJudgeAssociation.user_id == current_user.id)
    )
    if not is_assigned_human_judge:
        # Also ensure the user actually has the judge role
        if current_user.role != 'judge' or current_user.judge_type != 'human':
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a human judge.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Judge not assigned to this contest.")

    # 3. Validate submission IDs belong to the contest
    submission_ids_in_request = {vote.submission_id for vote in evaluation_data}
    contest_submission_ids_result = await db.scalars(
        select(models.Submission.id).where(models.Submission.contest_id == contest_id)
    )
    contest_submission_ids = set(contest_submission_ids_result.all())
    
    if not submission_ids_in_request.issubset(contest_submission_ids):
        invalid_ids = submission_ids_in_request - contest_submission_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid submission IDs provided that do not belong to this contest: {invalid_ids}"
        )
        
    # 4. Delete existing votes from this judge for this contest's submissions
    try:
        delete_stmt = (
            delete(models.Vote)
            .where(models.Vote.judge_id == current_user.id)
            .where(models.Vote.submission_id.in_(contest_submission_ids)) # Delete only votes for THIS contest
        )
        await db.execute(delete_stmt)
        # Don't commit yet, do it after adding new votes
    except Exception as e:
        await db.rollback()
        print(f"Error deleting previous votes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear previous evaluation.")

    # 5. Create new Vote records
    new_votes = []
    for vote_data in evaluation_data:
        new_vote = models.Vote(
            judge_id=current_user.id,
            submission_id=vote_data.submission_id,
            place=vote_data.place,
            comment=vote_data.comment,
            timestamp=datetime.utcnow(),
            app_version=settings.APP_VERSION # Add app version if available in settings
        )
        new_votes.append(new_vote)

    if not new_votes:
        # If evaluation_data was empty, still potentially cleared old votes
        await db.commit() # Commit the delete if it happened
        return {"message": "No evaluation data provided. Previous votes (if any) cleared."} 

    db.add_all(new_votes)
    
    # 6. Commit transaction
    try:
        await db.commit()
        for vote in new_votes: # Refresh needed if returning data, but not strictly necessary for 200 OK
             await db.refresh(vote)
        return {"message": f"Evaluation submitted successfully for {len(new_votes)} submissions."} # Return 200 OK with message
    except IntegrityError as e:
        await db.rollback()
        print(f"IntegrityError submitting evaluation: {e}")
        # Could be duplicate judge/submission pair if delete failed somehow, or FK issue
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database integrity error during vote creation.")
    except Exception as e:
        await db.rollback()
        print(f"Error submitting evaluation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save evaluation.")

# --- Contest Actions (Requires Authentication) ---

# @router.post("/{contest_id}/join", status_code=status.HTTP_200_OK)
# async def join_contest(contest_id: int, db: AsyncSession = Depends(get_db_session), current_user: models.User = Depends(get_current_active_user)):
#     """Allows a logged-in user to register interest or join a contest (if applicable)."""
#     # Implementation depends on contest rules (e.g., adding user to participants list)
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Joining contests not yet implemented")

# --- Contest Voting/Evaluation (Judge Only) ---

# @router.post("/{contest_id}/evaluate", status_code=status.HTTP_200_OK)
# async def submit_evaluation(contest_id: int, evaluation_data: List[schemas.VoteCreate], db: AsyncSession = Depends(get_db_session), current_user: models.User = Depends(get_current_active_user)):
#     """Allows an assigned judge to submit their votes/evaluation for a contest."""
#     # 1. Verify user is an assigned judge for this contest
#     # 2. Verify contest status is 'evaluation'
#     # 3. Process and save votes (handle potential duplicates/updates)
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Evaluation submission not yet implemented") 