from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select # Import select
from sqlalchemy.orm import noload, selectinload # UPDATED imports
from typing import List, Optional
from datetime import datetime, timezone
import openai # For type hinting client dependency
import anthropic # For type hinting client dependency

from ... import models, schemas # CORRECTED: Use three dots
from ...database import get_db_session # CORRECTED: Use three dots
from ... import security # CORRECTED: Use three dots
from ..dependencies import get_openai_client, get_anthropic_client, get_settings # Import client dependencies and settings
from ..config.settings import Settings # Import Settings for type hinting
from ..services import ai_service # Import the new AI service module

# --- Router for AI Writers ---
writer_router = APIRouter(
    prefix="/ai-writers",
    tags=["AI Agents", "AI Writers"],
    dependencies=[Depends(security.get_current_active_user)], # Require authentication for all endpoints here
)

@writer_router.post(
    "/", 
    response_model=schemas.UserAIWriterRead, 
    status_code=status.HTTP_201_CREATED,
    summary="Create User AI Writer",
    description="Creates a new AI Writer agent owned by the currently authenticated user."
)
async def create_user_ai_writer(
    writer_in: schemas.UserAIWriterCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Creates a new UserAIWriter record in the database.

    - **writer_in**: The AI Writer data to create.
    - **session**: The database session dependency.
    - **current_user**: The authenticated user dependency.
    """
    
    new_writer = models.UserAIWriter(
        **writer_in.model_dump(), 
        owner_id=current_user.id
    )
    
    session.add(new_writer)
    
    try:
        await session.commit()
        await session.refresh(new_writer)
        return new_writer
    except IntegrityError: # Catch potential unique constraint violation (name per user)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An AI Writer with the name '{writer_in.name}' already exists for this user."
        )
    except Exception as e: # Catch other potential DB errors
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the AI Writer: {e}" 
        )

# --- GET Endpoints --- 

@writer_router.get(
    "/", 
    response_model=List[schemas.UserAIWriterRead],
    summary="List User AI Writers",
    description="Lists AI Writer agents. Regular users see only their own agents. Admins can optionally filter by user_id or see all agents."
)
async def list_user_ai_writers(
    user_id: Optional[int] = None, # Admin-only query parameter
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Retrieves a list of UserAIWriter records.

    - **user_id**: (Admin only) Filter agents by owner ID.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    # --- Restore DB interaction ---
    query = select(models.UserAIWriter).options(noload(models.UserAIWriter.owner))
    
    if current_user.is_admin():
        if user_id:
            # Admin filtering by user ID
            query = query.where(models.UserAIWriter.owner_id == user_id)
        # Else: Admin sees all agents (no additional filter)
    else:
        # Regular user sees only their own agents
        if user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users can only list their own AI writers."
            )
        query = query.where(models.UserAIWriter.owner_id == current_user.id)
        
    query = query.order_by(models.UserAIWriter.name)
    
    try:
        result = await session.execute(query)
        writers = result.scalars().all()
        return writers
    except Exception as e:
        # Log the detailed error for debugging
        print(f"DATABASE ERROR in list_user_ai_writers: {e}") 
        # Reraise as an HTTPException for the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving AI writers: {e}"
        )
    # --- END Restore ---

@writer_router.get(
    "/{writer_id}", 
    response_model=schemas.UserAIWriterRead,
    summary="View User AI Writer Details",
    description="Retrieves details for a specific AI Writer agent. Requires ownership or admin privileges."
)
async def get_user_ai_writer(
    writer_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Retrieves a specific UserAIWriter by its ID.

    - **writer_id**: The ID of the writer to retrieve.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    writer = await session.get(models.UserAIWriter, writer_id)
    
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")

    # Check ownership or admin status
    if not current_user.is_admin() and writer.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this AI Writer")
        
    return writer

# --- PUT Endpoint ---

@writer_router.put(
    "/{writer_id}", 
    response_model=schemas.UserAIWriterRead,
    summary="Update User AI Writer",
    description="Updates details for a specific AI Writer agent. Requires ownership or admin privileges."
)
async def update_user_ai_writer(
    writer_id: int,
    writer_in: schemas.UserAIWriterUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Updates an existing UserAIWriter.

    - **writer_id**: The ID of the writer to update.
    - **writer_in**: The updated data.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    writer = await session.get(models.UserAIWriter, writer_id)
    
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")

    # Check ownership or admin status
    if not current_user.is_admin() and writer.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this AI Writer")

    # Update fields from the input schema
    update_data = writer_in.model_dump(exclude_unset=True) # Only include fields that were set
    for key, value in update_data.items():
        setattr(writer, key, value)
        
    # Ensure updated_at is modified
    writer.updated_at = datetime.now(timezone.utc)
    
    session.add(writer)
    
    try:
        await session.commit()
        await session.refresh(writer)
        return writer
    except IntegrityError: # Catch potential unique constraint violation (name per user)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An AI Writer with the name '{writer_in.name}' already exists for this user."
        )
    except Exception as e: # Catch other potential DB errors
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the AI Writer: {e}"
        )

# --- DELETE Endpoint ---

@writer_router.delete(
    "/{writer_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User AI Writer",
    description="Deletes a specific AI Writer agent. Requires ownership or admin privileges."
)
async def delete_user_ai_writer(
    writer_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Deletes a UserAIWriter.

    - **writer_id**: The ID of the writer to delete.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    writer = await session.get(models.UserAIWriter, writer_id)
    
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")

    # Check ownership or admin status
    if not current_user.is_admin() and writer.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this AI Writer")

    await session.delete(writer)
    try:
        await session.commit()
        # No content to return on successful delete
        return None # Return None for 204 response
    except Exception as e: # Catch potential DB errors during delete
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the AI Writer: {e}"
        )

# --- ADDED: AI Writer Action Endpoint ---
@writer_router.post(
    "/{writer_id}/generate", 
    response_model=schemas.AIWriterGenerateResponse, # Use the new response schema
    summary="Generate Text with User AI Writer",
    description="Triggers text generation using the specified User AI Writer, deducting credits."
)
async def generate_text_with_user_writer( # Renamed for clarity
    writer_id: int,
    request_data: schemas.AIWriterGenerateRequest, # Use the new request schema
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
    # Inject AI clients and settings
    settings: Settings = Depends(get_settings),
    openai_client: Optional[openai.AsyncOpenAI] = Depends(get_openai_client),
    anthropic_client: Optional[anthropic.AsyncAnthropic] = Depends(get_anthropic_client)
):
    """
    Generates text using a specific User AI Writer and deducts credits.

    - **writer_id**: The ID of the UserAIWriter to use.
    - **request_data**: Specifies the model_id to use for generation.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    - **settings**: Application settings dependency.
    - **openai_client**: OpenAI client dependency.
    - **anthropic_client**: Anthropic client dependency.
    """
    ledger_entry = None # Initialize ledger entry
    
    # Start transaction block
    try:
        # 1. Fetch the writer and verify ownership
        writer = await session.get(models.UserAIWriter, writer_id,
                                   options=[selectinload(models.UserAIWriter.owner)]) # Load owner for credits
        if not writer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
        
        if writer.owner_id != current_user.id:
            # Even admins cannot trigger *user-owned* agents directly (unless requirements change)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this AI Writer")

        # 2. Lock the user row for credit update
        # Fetch the owner directly with FOR UPDATE to ensure atomicity
        user_stmt = select(models.User).where(models.User.id == current_user.id).with_for_update()
        user_result = await session.execute(user_stmt)
        locked_user = user_result.scalar_one_or_none()
        if not locked_user:
             # This should not happen if current_user is valid, but defensive check
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        current_balance = locked_user.credits

        # 3. (Optional) Pre-check cost (can be complex, skip for now, rely on post-check)
        # model_config = ai_service.get_model_config(request_data.model_id, settings)
        # if model_config: ... estimate cost ...
        # if estimated_cost > current_balance: raise HTTPException(402...)

        # 4. Call the AI service function
        # Pass clients and settings to the service
        generation_result = await ai_service.perform_ai_generation(
            writer=writer,
            model_id=request_data.model_id,
            db=session, # Pass session if service needs it
            settings=settings,
            openai_client=openai_client,
            anthropic_client=anthropic_client,
            # generation_context= { ... } # Add context if needed
        )

        # 5. Handle AI service result
        if not generation_result['success']:
            # AI call failed, rollback is handled in finally, return error
            error_detail = generation_result.get('error', 'AI generation failed.')
            # Determine appropriate status code based on error type if possible
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE if "API Error" in error_detail else status.HTTP_500_INTERNAL_SERVER_ERROR
            raise HTTPException(status_code=status_code, detail=error_detail)
        
        # 6. AI call successful - Calculate Actual Credit Cost
        prompt_tokens = generation_result.get('prompt_tokens')
        completion_tokens = generation_result.get('completion_tokens')
        monetary_cost = generation_result.get('monetary_cost')
        generated_text = generation_result.get('generated_text')
        
        if prompt_tokens is None or completion_tokens is None:
             # This shouldn't happen if success is True, but handle defensively
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI service succeeded but token counts are missing.")

        actual_credit_cost = ai_service.calculate_credit_cost(
            monetary_cost=monetary_cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            settings=settings
        )

        # 7. Final Credit Check
        if current_balance < actual_credit_cost:
            # Not enough credits, rollback is handled in finally
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: {actual_credit_cost}, Available: {current_balance}"
            )

        # 8. Deduct Credits and Create CostLedger Entry
        locked_user.credits -= actual_credit_cost
        resulting_balance = locked_user.credits
        
        ledger_entry = models.CostLedger(
            user_id=locked_user.id,
            action_type='ai_generate',
            credits_change=-actual_credit_cost,
            real_cost=monetary_cost,
            description=f"Generation using User AI Writer '{writer.name}' (ID: {writer.id}) with model {request_data.model_id}. Tokens: P{prompt_tokens}/C{completion_tokens}.",
            related_entity_type='user_ai_writer',
            related_entity_id=writer.id,
            resulting_balance=resulting_balance
        )
        
        session.add(locked_user)
        session.add(ledger_entry)

        # 9. Commit Transaction
        await session.commit()
        await session.refresh(locked_user) # Refresh user to get updated balance if needed by response
        await session.refresh(ledger_entry) # Refresh ledger to get its ID

        # 10. Return Success Response
        return schemas.AIWriterGenerateResponse(
            action_type='ai_generate',
            user_id=locked_user.id,
            credits_spent=actual_credit_cost,
            remaining_credits=resulting_balance,
            real_cost=monetary_cost,
            cost_ledger_id=ledger_entry.id,
            generated_text=generated_text if generated_text is not None else "",
        )

    except HTTPException as http_exc:
        # If an HTTPException was raised (e.g., 403, 404, 402, 500/503 from AI fail),
        # rollback is handled in finally, just re-raise it.
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        print(f"ERROR during AI Generation endpoint: {e}")
        # Rollback handled in finally
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred during AI generation: {e}"
        )
    finally:
        # Ensure rollback if commit didn't happen or an error occurred before commit
        # Check if ledger_entry was created and committed successfully
        if ledger_entry is None or ledger_entry not in session:
             try:
                 # Check if session is active before rollback
                 if session.is_active:
                     await session.rollback()
                     print("Transaction rolled back due to error or insufficient funds in AI generation.")
             except Exception as rollback_err:
                 print(f"Error during rollback: {rollback_err}")
        # Always close the session if it was created by this endpoint scope
        # (FastAPI handles session closing with Depends(get_db_session))
        # await session.close() # Usually not needed with FastAPI Depends

# --- Router for AI Judges ---
judge_router = APIRouter(
    prefix="/ai-judges",
    tags=["AI Agents", "AI Judges"],
    dependencies=[Depends(security.get_current_active_user)],
)

@judge_router.post(
    "/",
    response_model=schemas.UserAIJudgeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create User AI Judge",
    description="Creates a new AI Judge agent owned by the currently authenticated user."
)
async def create_user_ai_judge(
    judge_in: schemas.UserAIJudgeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Creates a new UserAIJudge record in the database.

    - **judge_in**: The AI Judge data to create.
    - **session**: The database session dependency.
    - **current_user**: The authenticated user dependency.
    """
    new_judge = models.UserAIJudge(
        **judge_in.model_dump(), 
        owner_id=current_user.id
    )
    session.add(new_judge)
    try:
        await session.commit()
        await session.refresh(new_judge)
        return new_judge
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An AI Judge with the name '{judge_in.name}' already exists for this user."
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the AI Judge: {e}"
        )

@judge_router.get(
    "/",
    response_model=List[schemas.UserAIJudgeRead],
    summary="List User AI Judges",
    description="Lists AI Judge agents. Regular users see only their own agents. Admins can optionally filter by user_id or see all agents."
)
async def list_user_ai_judges(
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Retrieves a list of UserAIJudge records.

    - **user_id**: (Admin only) Filter agents by owner ID.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    # --- Restore DB interaction ---
    query = select(models.UserAIJudge).options(noload(models.UserAIJudge.owner))
    if current_user.is_admin():
        if user_id:
            query = query.where(models.UserAIJudge.owner_id == user_id)
    else:
        if user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users can only list their own AI judges."
            )
        query = query.where(models.UserAIJudge.owner_id == current_user.id)
    query = query.order_by(models.UserAIJudge.name)
    
    try:
        result = await session.execute(query)
        judges = result.scalars().all()
        return judges
    except Exception as e:
        # Log the detailed error for debugging
        print(f"DATABASE ERROR in list_user_ai_judges: {e}") 
        # Reraise as an HTTPException for the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving AI judges: {e}"
        )
    # --- END Restore ---

@judge_router.get(
    "/{judge_id}",
    response_model=schemas.UserAIJudgeRead,
    summary="View User AI Judge Details",
    description="Retrieves details for a specific AI Judge agent. Requires ownership or admin privileges."
)
async def get_user_ai_judge(
    judge_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Retrieves a specific UserAIJudge by its ID.

    - **judge_id**: The ID of the judge to retrieve.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    judge = await session.get(models.UserAIJudge, judge_id)
    
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")

    # Check ownership or admin status
    if not current_user.is_admin() and judge.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this AI Judge")
        
    return judge

@judge_router.put(
    "/{judge_id}",
    response_model=schemas.UserAIJudgeRead,
    summary="Update User AI Judge",
    description="Updates details for a specific AI Judge agent. Requires ownership or admin privileges."
)
async def update_user_ai_judge(
    judge_id: int,
    judge_in: schemas.UserAIJudgeUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Updates an existing UserAIJudge.

    - **judge_id**: The ID of the judge to update.
    - **judge_in**: The updated data.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    judge = await session.get(models.UserAIJudge, judge_id)
    
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")

    # Check ownership or admin status
    if not current_user.is_admin() and judge.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this AI Judge")

    # Update fields from the input schema
    update_data = judge_in.model_dump(exclude_unset=True) # Only include fields that were set
    for key, value in update_data.items():
        setattr(judge, key, value)
        
    # Ensure updated_at is modified
    judge.updated_at = datetime.now(timezone.utc)
    
    session.add(judge)
    
    try:
        await session.commit()
        await session.refresh(judge)
        return judge
    except IntegrityError: # Catch potential unique constraint violation (name per user)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An AI Judge with the name '{judge_in.name}' already exists for this user."
        )
    except Exception as e: # Catch other potential DB errors
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the AI Judge: {e}"
        )

@judge_router.delete(
    "/{judge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User AI Judge",
    description="Deletes a specific AI Judge agent. Requires ownership or admin privileges."
)
async def delete_user_ai_judge(
    judge_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Deletes a UserAIJudge.

    - **judge_id**: The ID of the judge to delete.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    """
    judge = await session.get(models.UserAIJudge, judge_id)
    
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")

    # Check ownership or admin status
    if not current_user.is_admin() and judge.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this AI Judge")

    await session.delete(judge)
    try:
        await session.commit()
        # No content to return on successful delete
        return None # Return None for 204 response
    except Exception as e: # Catch potential DB errors during delete
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the AI Judge: {e}"
        )

# --- ADDED: AI Judge Action Endpoint ---
@judge_router.post(
    "/{judge_id}/evaluate", 
    response_model=schemas.AIJudgeEvaluateResponse, # Use the new response schema
    summary="Evaluate Contest with User AI Judge",
    description="Triggers contest evaluation using the specified User AI Judge, deducting credits."
)
async def evaluate_submissions_with_user_judge( # Renamed for clarity
    judge_id: int,
    request_data: schemas.AIJudgeEvaluateRequest, # Use the new request schema
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
     # Inject AI clients and settings
    settings: Settings = Depends(get_settings),
    openai_client: Optional[openai.AsyncOpenAI] = Depends(get_openai_client),
    anthropic_client: Optional[anthropic.AsyncAnthropic] = Depends(get_anthropic_client)
):
    """
    Evaluates contest submissions using a specific User AI Judge and deducts credits.

    - **judge_id**: The ID of the UserAIJudge to use.
    - **request_data**: Specifies the contest_id and model_id to use.
    - **session**: Database session dependency.
    - **current_user**: Authenticated user dependency.
    - **settings**: Application settings dependency.
    - **openai_client**: OpenAI client dependency.
    - **anthropic_client**: Anthropic client dependency.
    """
    ledger_entry = None # Initialize ledger entry
    evaluation_successful = False # Track if AI evaluation part succeeded
    db_votes_prepared = False # Track if Vote objects were added to session

    try:
        # 1. Fetch the judge and verify ownership
        judge = await session.get(models.UserAIJudge, judge_id,
                                  options=[selectinload(models.UserAIJudge.owner)]) # Load owner for credits
        if not judge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
            
        if judge.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this AI Judge")

        # 2. Lock the user row for credit update
        user_stmt = select(models.User).where(models.User.id == current_user.id).with_for_update()
        user_result = await session.execute(user_stmt)
        locked_user = user_result.scalar_one_or_none()
        if not locked_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        current_balance = locked_user.credits
        contest_id = request_data.contest_id
        model_id = request_data.model_id

        # 3. (Optional) Pre-check (Skipped for now)

        # 4. Call the AI service function for evaluation
        evaluation_result = await ai_service.perform_ai_evaluation(
            judge=judge,
            contest_id=contest_id,
            model_id=model_id,
            db=session, # Pass the session for DB operations within the service
            settings=settings,
            openai_client=openai_client,
            anthropic_client=anthropic_client
        )
        
        evaluation_successful = evaluation_result['success']
        db_votes_prepared = evaluation_result.get('db_votes_added', False)

        # 5. Handle AI service result
        if not evaluation_successful:
            error_detail = evaluation_result.get('error', 'AI evaluation failed.')
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE if "API Error" in error_detail else status.HTTP_500_INTERNAL_SERVER_ERROR
            # If DB votes were prepared but something else failed, rollback occurs in finally
            raise HTTPException(status_code=status_code, detail=error_detail)
        
        # Check if votes were actually prepared by the service
        if not db_votes_prepared:
             # This might indicate an issue like no submissions found, handled within the service
             # The service should return success=False in such cases, but double-check
              raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                detail="AI evaluation service reported success but failed to prepare votes.")

        # 6. AI call successful - Calculate Actual Credit Cost
        prompt_tokens = evaluation_result.get('prompt_tokens')
        completion_tokens = evaluation_result.get('completion_tokens')
        monetary_cost = evaluation_result.get('monetary_cost')
        status_message = evaluation_result.get('status_message', 'Evaluation completed.')
        # parsed_votes_data = evaluation_result.get('parsed_votes', []) # For logging/context

        if prompt_tokens is None or completion_tokens is None:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI service succeeded but token counts are missing.")

        actual_credit_cost = ai_service.calculate_credit_cost(
            monetary_cost=monetary_cost,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            settings=settings
        )

        # 7. Final Credit Check
        if current_balance < actual_credit_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: {actual_credit_cost}, Available: {current_balance}"
            )

        # 8. Deduct Credits and Create CostLedger Entry
        locked_user.credits -= actual_credit_cost
        resulting_balance = locked_user.credits
        
        ledger_entry = models.CostLedger(
            user_id=locked_user.id,
            action_type='ai_evaluate',
            credits_change=-actual_credit_cost,
            real_cost=monetary_cost,
            description=f"Evaluation for Contest ID {contest_id} using User AI Judge '{judge.name}' (ID: {judge.id}) with model {model_id}. Tokens: P{prompt_tokens}/C{completion_tokens}.",
            related_entity_type='user_ai_judge',
            related_entity_id=judge.id,
            # Add related contest info?
            # related_entity_type_2='contest', # Need a better way if multiple relations
            # related_entity_id_2=contest_id, 
            resulting_balance=resulting_balance
        )
        
        session.add(locked_user)
        session.add(ledger_entry)
        # Vote objects were already added to the session by the service function

        # 9. Commit Transaction (includes user credit update, ledger entry, AND the votes)
        await session.commit()
        await session.refresh(locked_user)
        await session.refresh(ledger_entry)
        # Refreshing Vote objects is usually not necessary unless needed in response

        # 10. Return Success Response
        return schemas.AIJudgeEvaluateResponse(
            action_type='ai_evaluate',
            user_id=locked_user.id,
            credits_spent=actual_credit_cost,
            remaining_credits=resulting_balance,
            real_cost=monetary_cost,
            cost_ledger_id=ledger_entry.id,
            contest_id=contest_id,
            evaluation_status='completed', # Assuming sync completion for now
            message=status_message,
        )

    except HTTPException as http_exc:
        # If an HTTPException was raised (403, 404, 402, 50x), rollback handled in finally.
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        print(f"ERROR during AI Evaluation endpoint: {e}")
        # Rollback handled in finally
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred during AI evaluation: {e}"
        )
    finally:
        # Ensure rollback if commit didn't happen or an error occurred
        # Check if ledger_entry was created and committed successfully
        if ledger_entry is None or ledger_entry not in session:
            try:
                 # Check if session is active before rollback
                 if session.is_active:
                    await session.rollback()
                    print("Transaction rolled back due to error or insufficient funds in AI evaluation.")
            except Exception as rollback_err:
                 print(f"Error during rollback: {rollback_err}")
        # await session.close() # Handled by FastAPI Depends