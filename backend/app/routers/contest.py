from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from sqlalchemy import or_, delete
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Relative imports
from ... import models, schemas
from ...database import get_db_session
from ...security import (
    get_current_active_user,
    get_optional_current_user,
    require_admin,
    create_access_token,
)
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
    summary="Create a new contest (User or Admin)", # Updated summary
    tags=["Contests"]
)
async def create_contest(
    contest_data: schemas.ContestCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Changed dependency
):
    """Creates a new contest.

    Requires authenticated user (user or admin).
    Sets the current user as the contest creator.
    Handles password hashing if contest_type is 'private'.
    """
    # Authorization check (logged in) is handled by the dependency

    contest_dict = contest_data.model_dump(exclude_unset=True)
    password = contest_dict.pop('password', None)

    # Set the creator_id from the authenticated user
    contest_dict['creator_id'] = current_user.id 

    new_contest = models.Contest(**contest_dict)

    # Handle password hashing
    if new_contest.contest_type == 'private' and password:
        new_contest.set_password(password)
    elif new_contest.contest_type == 'public':
        new_contest.password_hash = None

    db.add(new_contest)
    await db.commit()
    await db.refresh(new_contest)
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
    # current_user: Optional[models.User] = Depends(get_optional_current_user) # No longer needed for listing
):
    """Retrieves a list of all contests (public and private).

    Access control is handled when viewing contest details or participating.
    """
    # Base query - simplified, no access control needed here
    stmt = select(models.Contest).order_by(models.Contest.created_at.desc()) # Order by creation date as per spec

    # Apply status filter if provided
    if status:
        stmt = stmt.where(models.Contest.status == status)

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
            selectinload(models.Contest.submissions),    # Eager load submissions
            selectinload(models.Contest.human_judges),   # Eager load human judges
            selectinload(models.Contest.ai_judges)       # Eager load AI judges
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
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[models.User] = Depends(get_optional_current_user)
):
    """Retrieves detailed information about a specific contest.

    - Public contests are accessible to everyone.
    - Private contests require admin/judge role OR a valid access token 
      (obtained via POST /check-password) passed as a cookie.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Access Control for Private Contests --- 
    if contest.contest_type == 'private':
        is_authorized = False
        expected_subject = f"contest_access:{contest_id}"

        # 1. Check for Admin/Judge role
        if current_user:
            if current_user.is_admin():
                is_authorized = True
            # Check if user is in the list of assigned human judges
            elif current_user in contest.human_judges: 
                is_authorized = True

        # 2. If not authorized by role, check for password access token (cookie)
        if not is_authorized:
            token = request.cookies.get(f"contest_access_{contest_id}")
            if token:
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    subject: str = payload.get("sub")
                    if subject == expected_subject:
                        is_authorized = True # Token is valid for this contest
                except JWTError: # Catches expired tokens, invalid signatures, etc.
                    pass # Token is invalid, authorization remains False

        # 3. Final check - raise 403 if not authorized by role or valid token
        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Private contest. Use POST /contests/{contest_id}/check-password to gain temporary access."
            )
    # --- End Access Control --- 

    return contest

@router.put(
    "/{contest_id}",
    response_model=schemas.ContestPublic,
    summary="Update a contest (Owner or Admin)", # Updated summary
    tags=["Contests"]
)
async def update_contest(
    contest_id: int,
    contest_update: schemas.ContestUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Changed dependency
):
    """Updates an existing contest.

    - Requires admin privileges OR ownership of the contest.
    """
    contest = await get_contest_or_404(contest_id, db) # Fetch existing contest

    # --- Authorization Check ---
    if not current_user.is_admin() and contest.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this contest"
        )
    # --- End Authorization Check ---

    update_data = contest_update.model_dump(exclude_unset=True)

    # Handle password update if provided
    new_password = update_data.pop("password", None)
    if contest.contest_type == 'private' and new_password:
        contest.set_password(new_password) # Use the passlib method
    elif "contest_type" in update_data and update_data["contest_type"] == 'public':
        # If changing to public, ensure password hash is cleared
        contest.password_hash = None 

    # Update other contest fields
    for field, value in update_data.items():
        setattr(contest, field, value)

    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest

@router.delete(
    "/{contest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contest (Owner or Admin)", # Updated summary
    tags=["Contests"]
)
async def delete_contest(
    contest_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Changed dependency
):
    """Deletes a contest and its associated data (submissions, votes, etc.).

    - Requires admin privileges OR ownership of the contest.
    """
    contest = await get_contest_or_404(contest_id, db)

    # --- Authorization Check ---
    if not current_user.is_admin() and contest.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this contest"
        )
    # --- End Authorization Check ---

    await db.delete(contest)
    await db.commit()
    # No need to return Response(status_code=...) explicitly for 204
    # Returning None with status_code in decorator handles it.
    return None 

# --- Submit to Contest ---

@router.post("/{contest_id}/submissions", response_model=schemas.SubmissionRead, status_code=status.HTTP_201_CREATED, summary="Submit an Entry to a Contest")
async def create_submission(
    contest_id: int,
    submission_data: schemas.SubmissionCreate,
    request: Request, # Add request
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) # Changed dependency
):
    """Creates a new submission for a contest.

    - Requires authenticated user.
    - If user is not admin:
        - Contest must be 'open'.
        - If contest is private, requires a valid access cookie 
          (from POST /check-password).
    - Admins can submit to contests in any status.
    """
    contest = await get_contest_or_404(contest_id, db) # Use helper to get contest or 404

    # --- Authorization and Status Checks ---
    is_authorized_for_private = True # Assume public or authorized initially
    
    if not current_user.is_admin():
        # 1. Check Contest Status (Non-Admin)
        if contest.status != 'open':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest is not open for submissions"
            )
        
        # 2. Check Private Contest Access (Non-Admin)
        if contest.contest_type == 'private':
            is_authorized_for_private = False # Reset flag, must verify token
            expected_subject = f"contest_access:{contest_id}"
            token = request.cookies.get(f"contest_access_{contest_id}")
            if token:
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    subject: str = payload.get("sub")
                    if subject == expected_subject:
                        is_authorized_for_private = True # Token is valid
                except JWTError:
                    pass # Token invalid, flag remains False

            if not is_authorized_for_private:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Private contest. Use POST /contests/{contest_id}/check-password first."
                )
    # --- End Authorization and Status Checks ---
    
    # --- TODO: Add contest specific rule checks (Non-Admin) ---
    # if not current_user.is_admin():
    #     # - Check if judges can participate (if contest.restrict_judges_as_authors)
    #     if contest.restrict_judges_as_authors and current_user in contest.judges:
    #          raise HTTPException(status_code=403, detail="Judges cannot submit entries to this contest.")
    #     # - Check if multiple submissions allowed per author (if contest.allow_multiple_submissions_per_author is False)
    #     # Requires querying existing submissions for this user in this contest

    # Prepare submission data
    submission_dict = submission_data.model_dump(exclude_unset=True)
    submission_dict['user_id'] = current_user.id
    submission_dict['contest_id'] = contest_id
    
    # Use username as default author_name if not provided
    if 'author_name' not in submission_dict or not submission_dict['author_name']:
        submission_dict['author_name'] = current_user.username
        
    # Calculate word count
    submission_dict['word_count'] = len(submission_dict.get('text_content', '').split())

    # Create and save
    new_submission = models.Submission(**submission_dict)
    db.add(new_submission)
    try:
        await db.commit()
        await db.refresh(new_submission)
    except IntegrityError as e:
        await db.rollback()
        # Log the error details for debugging
        print(f"IntegrityError creating submission for contest {contest_id} by user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error saving submission (potential duplicate or constraint violation).")
    except Exception as e:
        await db.rollback()
        print(f"Exception creating submission for contest {contest_id} by user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while saving the submission.")
        
    return new_submission

# --- Get Submissions for a Contest (Judge/Admin Access) ---
@router.get("/{contest_id}/submissions", response_model=List[schemas.SubmissionRead], summary="List Submissions for a Contest") 
async def list_contest_submissions(
    contest_id: int,
    request: Request, # Add request object
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user) 
):
    """Lists submissions for a contest, handling access control and anonymization.

    Access Rules:
    - Admins: Can view anytime.
    - Non-Admins:
        - Can view only if contest status is 'evaluation' or 'closed'.
        - AND must EITHER be an assigned judge OR have access to the private contest (via cookie if private).
    
    Anonymization:
    - Author names are anonymized if contest status is NOT 'closed' 
      AND the current user is NOT an admin.
    """
    contest = await get_contest_or_404(contest_id, db) # Eager loads judges and submissions

    # --- Authorization Check --- 
    can_view = False
    is_private_contest_accessible = True # Assume public or accessible initially

    if current_user.is_admin():
        can_view = True
    else:
        # Non-admin access requires specific conditions
        if contest.status in ['evaluation', 'closed']:
            # Condition 1: User is an assigned judge
            is_judge = current_user in contest.judges

            # Condition 2: User has access to the contest (relevant if private)
            if contest.contest_type == 'private' and not is_judge:
                is_private_contest_accessible = False # Must verify cookie
                expected_subject = f"contest_access:{contest_id}"
                token = request.cookies.get(f"contest_access_{contest_id}")
                if token:
                    try:
                        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                        subject: str = payload.get("sub")
                        if subject == expected_subject:
                            is_private_contest_accessible = True
                    except JWTError:
                        pass # Invalid token
            
            # User can view if they are a judge OR have access to the (potentially private) contest
            if is_judge or is_private_contest_accessible:
                can_view = True

    if not can_view:
        detail_message = "Access denied to view submissions."
        if contest.status == 'open' and not current_user.is_admin():
            detail_message = "Submissions cannot be viewed while the contest is open."
        elif not is_private_contest_accessible and not (current_user in contest.judges):
             detail_message = "Access denied: User lacks permissions or required access for this contest state."
       
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_message
        )
    # --- End Authorization Check ---

    # --- Anonymization Logic ---
    submissions_to_return = []
    # Anonymize if contest is not closed AND user is not admin
    should_anonymize = (contest.status != 'closed') and (not current_user.is_admin())

    for sub in contest.submissions:
        # Convert ORM object to Pydantic model for manipulation/return
        sub_data = schemas.SubmissionRead.model_validate(sub)
        if should_anonymize:
            # Use a generic placeholder or ID
            sub_data.author_name = f"Author #{sub.id}" 
        submissions_to_return.append(sub_data)

    return submissions_to_return

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