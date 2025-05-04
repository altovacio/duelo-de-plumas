from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select # Import select
from sqlalchemy.orm import noload # NEW: Import noload
from typing import List, Optional
from datetime import datetime, timezone

from ... import models, schemas # CORRECTED: Use three dots
from ...database import get_db_session # CORRECTED: Use three dots
from ... import security # CORRECTED: Use three dots

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
async def generate_text(
    writer_id: int,
    request_data: schemas.AIWriterGenerateRequest, # Use the new request schema
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
    # Assuming AI service dependencies are available or need to be added
    # openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client), 
    # anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
):
    """
    Executes text generation using a user-owned AI Writer.
    Requires ownership.
    Checks credits, performs generation, deducts credits, and logs to CostLedger.
    """
    # 1. Verify Ownership
    writer = await session.get(models.UserAIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    if writer.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this AI Writer")

    # --- Transaction Start --- 
    try:
        # 2. Lock user row and get current credits
        user_result = await session.execute(
            select(models.User).where(models.User.id == current_user.id).with_for_update()
        )
        user_to_charge = user_result.scalar_one()
        current_balance = user_to_charge.credits

        # 3. Estimate Cost (Placeholder - Requires actual cost calculation logic)
        # This is tricky before the actual API call. Maybe use a fixed estimate or a rate?
        # For now, let's assume a placeholder cost or skip pre-check and rely on post-check.
        estimated_cost_credits = 10 # Placeholder: Replace with actual estimation logic
        
        # 4. Pre-check Credits (Optional but recommended)
        if current_balance < estimated_cost_credits:
             raise HTTPException(
                 status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                 detail=f"Insufficient credits. Estimated cost: {estimated_cost_credits}, Balance: {current_balance}"
             )

        # 5. Execute AI Generation Call (Placeholder - Requires AI service integration)
        # This function should return the generated text, actual token usage, and real monetary cost.
        # ai_result = await ai_services.call_writer_generation(
        #     writer=writer, 
        #     model_id=request_data.model_id, 
        #     # Pass other params from request_data... 
        # )
        # Placeholder result:
        ai_result = {
            "success": True,
            "generated_text": f"Generated text using {writer.name} and model {request_data.model_id}.",
            "prompt_tokens": 150,
            "completion_tokens": 300,
            "real_cost_usd": 0.0015 # Example real cost
        }
        
        if not ai_result.get("success"): 
             # Rollback needed? Probably not as nothing committed yet.
             raise HTTPException(status_code=500, detail="AI generation failed.") # Improve error handling

        # 6. Calculate Actual Credit Cost (Placeholder - Requires cost model)
        # Map real_cost_usd or token usage to credit cost.
        # Example: 1000 credits per $0.01 USD?
        real_cost = ai_result.get("real_cost_usd")
        # Simple placeholder: 1 credit per 100 total tokens? Or based on real_cost?
        actual_credit_cost = (ai_result["prompt_tokens"] + ai_result["completion_tokens"]) // 100 # PLACEHOLDER
        if actual_credit_cost <= 0: actual_credit_cost = 1 # Minimum cost of 1 credit?

        # 7. Final Credit Check (Crucial after getting actual cost)
        if current_balance < actual_credit_cost:
            # Rollback likely not needed as nothing is committed yet.
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                detail=f"Insufficient credits for actual cost. Required: {actual_credit_cost}, Balance: {current_balance}"
            )

        # 8. Deduct Credits and Update User
        new_balance = current_balance - actual_credit_cost
        user_to_charge.credits = new_balance
        session.add(user_to_charge)

        # 9. Create CostLedger Entry
        ledger_entry = models.CostLedger(
            user_id=user_to_charge.id,
            action_type='ai_generate',
            credits_change=-actual_credit_cost,
            real_cost=real_cost,
            description=f"AI generation using writer '{writer.name}' (ID: {writer.id}) with model {request_data.model_id}.",
            related_entity_type='user_ai_writer',
            related_entity_id=writer.id,
            resulting_balance=new_balance
            # Consider adding tokens to description or separate fields if needed
        )
        session.add(ledger_entry)

        # 10. Commit Transaction
        await session.commit()
        await session.refresh(user_to_charge) # Refresh to get potentially updated state
        await session.refresh(ledger_entry) # Refresh to get the ledger entry ID

        # 11. Return Success Response
        return schemas.AIWriterGenerateResponse(
            action_type='ai_generate',
            user_id=user_to_charge.id,
            credits_spent=actual_credit_cost,
            remaining_credits=new_balance,
            real_cost=real_cost,
            cost_ledger_id=ledger_entry.id,
            generated_text=ai_result["generated_text"]
        )

    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        await session.rollback() # Ensure rollback on handled errors too
        raise http_exc
    except Exception as e: # Catch unexpected errors
        await session.rollback()
        # Log the error for debugging
        print(f"ERROR during AI generation for user {current_user.id}, writer {writer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during AI generation: {e}"
        )
    # --- Transaction End ---

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
async def evaluate_submissions(
    judge_id: int,
    request_data: schemas.AIJudgeEvaluateRequest, # Use the new request schema
    session: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(security.get_current_active_user),
    # Assuming AI service dependencies are available or need to be added
    # openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client), 
    # anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
):
    """
    Executes contest evaluation using a user-owned AI Judge.
    Requires ownership.
    Checks credits, performs evaluation, deducts credits, and logs to CostLedger.
    """
    # 1. Verify Ownership
    judge = await session.get(models.UserAIJudge, judge_id)
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    if judge.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this AI Judge")

    # --- Transaction Start ---
    try:
        # 2. Lock user row and get current credits
        user_result = await session.execute(
            select(models.User).where(models.User.id == current_user.id).with_for_update()
        )
        user_to_charge = user_result.scalar_one()
        current_balance = user_to_charge.credits

        # 3. Estimate Cost (Placeholder - Requires actual cost calculation logic based on contest/submissions)
        estimated_cost_credits = 50 # Placeholder: Replace with actual estimation logic
        
        # 4. Pre-check Credits (Optional)
        if current_balance < estimated_cost_credits:
             raise HTTPException(
                 status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                 detail=f"Insufficient credits. Estimated cost: {estimated_cost_credits}, Balance: {current_balance}"
             )

        # 5. Execute AI Evaluation Call (Placeholder - Requires AI service integration)
        # This function should handle evaluating submissions for the contest_id,
        # return status, actual token usage, and real monetary cost.
        # ai_result = await ai_services.call_judge_evaluation(
        #     judge=judge, 
        #     contest_id=request_data.contest_id,
        #     model_id=request_data.model_id,
        #     # Pass other params...
        # )
        # Placeholder result:
        ai_result = {
            "success": True,
            "status": "completed",
            "message": f"Evaluation for contest {request_data.contest_id} completed successfully by {judge.name}.",
            "prompt_tokens": 1500,
            "completion_tokens": 3000,
            "real_cost_usd": 0.015 
        }

        if not ai_result.get("success"): 
             raise HTTPException(status_code=500, detail=ai_result.get("message", "AI evaluation failed."))

        # 6. Calculate Actual Credit Cost (Placeholder)
        real_cost = ai_result.get("real_cost_usd")
        actual_credit_cost = (ai_result["prompt_tokens"] + ai_result["completion_tokens"]) // 100 # PLACEHOLDER
        if actual_credit_cost <= 0: actual_credit_cost = 1 

        # 7. Final Credit Check
        if current_balance < actual_credit_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                detail=f"Insufficient credits for actual cost. Required: {actual_credit_cost}, Balance: {current_balance}"
            )

        # 8. Deduct Credits and Update User
        new_balance = current_balance - actual_credit_cost
        user_to_charge.credits = new_balance
        session.add(user_to_charge)

        # 9. Create CostLedger Entry
        ledger_entry = models.CostLedger(
            user_id=user_to_charge.id,
            action_type='ai_evaluate',
            credits_change=-actual_credit_cost,
            real_cost=real_cost,
            description=f"AI evaluation for contest {request_data.contest_id} using judge '{judge.name}' (ID: {judge.id}) with model {request_data.model_id}.",
            related_entity_type='user_ai_judge',
            related_entity_id=judge.id,
            resulting_balance=new_balance
        )
        session.add(ledger_entry)

        # 10. Commit Transaction
        await session.commit()
        await session.refresh(user_to_charge)
        await session.refresh(ledger_entry)

        # 11. Return Success Response
        return schemas.AIJudgeEvaluateResponse(
            action_type='ai_evaluate',
            user_id=user_to_charge.id,
            credits_spent=actual_credit_cost,
            remaining_credits=new_balance,
            real_cost=real_cost,
            cost_ledger_id=ledger_entry.id,
            contest_id=request_data.contest_id,
            evaluation_status=ai_result["status"],
            message=ai_result["message"]
        )

    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        await session.rollback()
        raise http_exc
    except Exception as e: # Catch unexpected errors
        await session.rollback()
        print(f"ERROR during AI evaluation for user {current_user.id}, judge {judge_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during AI evaluation: {e}"
        )
    # --- Transaction End ---