from typing import List
from fastapi import APIRouter, HTTPException

from app.utils.ai_models import get_available_models, get_model_by_id, AIModel

router = APIRouter()

@router.get("", response_model=List[AIModel])
async def get_available_llm_models(
):
    """
    Get all available LLM models.
    Returns models that are currently enabled in the system with their pricing information.
    """
    return get_available_models()

@router.get("/{model_id}", response_model=AIModel)
async def get_llm_model_details(
    model_id: str,
):
    """
    Get technical details and pricing information about a specific LLM model.
    Returns id, name, provider, context window size, and pricing information.
    """
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return model 