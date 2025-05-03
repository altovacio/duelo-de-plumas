from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from ... import models, schemas
from ...database import get_db_session
from ...security import get_current_active_user

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
    responses={404: {"description": "Not found"}},
)

async def get_submission_for_user_or_admin(
    submission_id: int, 
    db: AsyncSession, 
    current_user: models.User
) -> models.Submission:
    """Helper to get submission, load contest, check ownership or admin status."""
    result = await db.execute(
        select(models.Submission)
        .options(selectinload(models.Submission.contest)) # Load contest relationship
        .where(models.Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()

    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Authorization check: Must be admin or the user who submitted it
    if not current_user.is_admin() and submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )
    
    # Check if contest relationship was loaded (should be, but defensive check)
    if submission.contest is None:
         # This indicates a data integrity issue or loading problem
         print(f"Error: Contest relationship not loaded for submission {submission_id}")
         raise HTTPException(status_code=500, detail="Internal server error: Could not load contest data.")
         
    return submission

@router.delete(
    "/{submission_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or Withdraw Submission (Owner or Admin)"
)
async def delete_or_withdraw_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deletes or withdraws a specific submission.

    - **Admins:** Can delete any submission directly (hard delete).
    - **Owners (Users):**
        - If the contest is 'open', the submission is deleted (hard delete).
        - If the contest is 'evaluation' or 'closed', the submission text is 
          replaced with '[TEXTO RETIRADO POR EL AUTOR]' and title is updated (soft delete/withdrawal).
    """
    submission = await get_submission_for_user_or_admin(submission_id, db, current_user)
    contest_status = submission.contest.status

    if current_user.is_admin():
        # Admins always hard delete
        await db.delete(submission)
        await db.commit()
        print(f"Admin {current_user.username} deleted submission {submission_id}.")
    
    elif submission.user_id == current_user.id:
        # User owns the submission, apply state logic
        if contest_status == 'open':
            await db.delete(submission)
            await db.commit()
            print(f"User {current_user.username} deleted submission {submission_id} (contest open).")
        elif contest_status in ['evaluation', 'closed']:
            # Withdraw the submission
            submission.text_content = "[TEXTO RETIRADO POR EL AUTOR]"
            submission.title = f"[Retirado] {submission.title}"[:150] # Mark title, ensure max length
            # Optionally clear votes? Spec doesn't mention, leave votes for now.
            # Optionally set a flag? No flag exists, text change is indicator.
            db.add(submission)
            await db.commit()
            await db.refresh(submission) # Refresh to confirm changes if needed
            print(f"User {current_user.username} withdrew submission {submission_id} (contest {contest_status}).")
        else:
            # Should not happen with standard statuses, but safety check
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete or withdraw submission in contest state: {contest_status}"
            )
    else:
         # This case should be caught by get_submission_for_user_or_admin, but defensive check
         raise HTTPException(status_code=403, detail="Forbidden")

    # Return No Content response
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Add other submission-related endpoints here if needed (e.g., GET specific submission) 