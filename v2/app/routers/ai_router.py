from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import openai
import anthropic

# Fix dependency imports based on what's available
# from ..dependencies import get_openai_client_mock as get_openai_client # Remove mock
# from ..dependencies import get_anthropic_client_mock as get_anthropic_client # Remove mock
from ..dependencies import get_openai_client, get_anthropic_client # Import real clients
# Import a mock DB session for testing since the real one doesn't exist yet
# from unittest.mock import AsyncMock # Remove mock import
from ...database import get_db_session # Corrected: Go up two levels

# Temporary mock session dependency until real implementation is ready
# async def get_async_db_session(): # Remove mock function
#     """Temporary mock database session for testing."""
#     session = AsyncMock(spec=AsyncSession)
#     try:
#         yield session
#     finally:
#         await session.close()

from ..schemas.ai_schemas import GenerateTextRequest, GenerateTextResponse, AIEvaluationResult
from ..services import ai_services # Import the ai_services module

router = APIRouter(
    tags=["AI"],
)

@router.post("/generate-text", response_model=GenerateTextResponse)
async def generate_text_endpoint(
    request_data: GenerateTextRequest,
    session: AsyncSession = Depends(get_db_session), # Use real DB session
    openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client),
    anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
):
    """
    Generate text using an AI writer based on contest details and submit it.
    """
    # MOCK IMPLEMENTATION FOR TESTING - REMOVE THIS BLOCK
    # This skips the database access and returns mock data
    # 
    # if request_data.contest_id == 999:
    #     # Simulate "contest not found" error
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Contest with ID {request_data.contest_id} not found"
    #     )
    # 
    # if request_data.ai_writer_id == 999:
    #     # Simulate "AI writer not found" error
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"AI Writer with ID {request_data.ai_writer_id} not found"
    #     )
    # 
    # # You can customize responses based on different inputs for testing
    # mock_text = f"This is a mock generated text for the title '{request_data.title}' using model {request_data.model_id}. "
    # mock_text += "It was a cold night in the city, and the rain was falling steadily. The detective pulled his coat tighter "
    # mock_text += "around himself as he walked down the dimly lit street. The case had been troubling him for weeks, and he "
    # mock_text += "was no closer to solving it than when he started. But tonight, something felt different. As he approached "
    # mock_text += "the old abandoned warehouse, he noticed a faint light coming from inside..."
    # 
    # # Return a successful response
    # return GenerateTextResponse(
    #     success=True,
    #     message="Text generated and submitted successfully (MOCK DATA)",
    #     submission_id=42,
    #     text=mock_text
    # )

    # ORIGINAL IMPLEMENTATION - Uncomment when database is ready
    result = await ai_services.generate_text(
        session=session,
        contest_id=request_data.contest_id,
        ai_writer_id=request_data.ai_writer_id,
        model_id=request_data.model_id,
        title=request_data.title,
        openai_client=openai_client,
        anthropic_client=anthropic_client
    )
    
    if not result["success"]:
        # Determine appropriate status code based on message? Or just 400?
        status_code = status.HTTP_400_BAD_REQUEST 
        if "not found" in result["message"].lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "not open" in result["message"].lower():
             status_code = status.HTTP_409_CONFLICT
        elif "error calling ai api" in result["message"].lower():
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE # Or 500?
        raise HTTPException(status_code=status_code, detail=result["message"])
        
    return GenerateTextResponse(**result)


@router.post("/evaluate-contest/{contest_id}", response_model=AIEvaluationResult)
async def evaluate_contest_endpoint(
    contest_id: int,
    judge_id: int, # Assuming judge_id is passed as a query parameter or in request body
    session: AsyncSession = Depends(get_db_session), # Use real DB session
    openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client),
    anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
) -> AIEvaluationResult:
    """
    Triggers AI evaluation for a specific contest using a designated AI judge.
    """
    # MOCK IMPLEMENTATION FOR TESTING - REMOVE THIS BLOCK
    # if contest_id == 999:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Contest with ID {contest_id} not found"
    #     )
    #     
    # if judge_id == 999:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"AI Judge with ID {judge_id} not found"
    #     )
    # 
    # # Generate mock rankings and comments
    # mock_rankings = {"42": 1, "43": 2, "44": 3}
    # mock_comments = {
    #     "42": "This submission demonstrated exceptional creativity and mastery of language...",
    #     "43": "A compelling narrative with strong character development...",
    #     "44": "While the story had an interesting premise, the execution lacked depth..."
    # }
    # 
    # # Return mock data
    # return AIEvaluationResult(
    #     success=True,
    #     message="Contest evaluation completed successfully (MOCK DATA)",
    #     evaluation_id=15,
    #     judge_id=judge_id,
    #     contest_id=contest_id,
    #     rankings=mock_rankings,
    #     comments=mock_comments
    # )

    # ORIGINAL IMPLEMENTATION - Uncomment when database is ready
    try:
        result = await ai_services.run_ai_evaluation(
            contest_id=contest_id,
            judge_id=judge_id,
            session=session,
            openai_client=openai_client,
            anthropic_client=anthropic_client,
            # Potentially pass temperature from config or request
        )
        
        if not result["success"]:
             # Refine error handling based on ai_services logic
             status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
             if "not found" in result.get("message", "").lower():
                 status_code = status.HTTP_404_NOT_FOUND
             elif "invalid state" in result.get("message", "").lower(): # Example condition
                 status_code = status.HTTP_409_CONFLICT
             raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "AI evaluation failed.")
            )
            
        # Return the detailed results from the service
        return AIEvaluationResult(**result)
    
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the exception details
        print(f"Error during AI evaluation endpoint: {e}") # Consider using proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during AI evaluation."
        ) 