"""
Module for handling AI model configurations and selections.
This provides utility functions for working with AI models and their cost structures.
"""

import json
import os
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel


class ModelProvider(str, Enum):
    """Enum for AI model providers"""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GOOGLE = "Google"
    COHERE = "Cohere"
    META = "Meta"
    DEEPSEEK = "DeepSeek"
    XAI = "xAI"


class AIModel(BaseModel):
    """Representation of an AI model and its cost structure"""
    id: str
    name: str
    provider: ModelProvider
    context_window_k: int
    input_cost_usd_per_1k_tokens: float
    output_cost_usd_per_1k_tokens: float
    available: bool


# Load model definitions from JSON
_models_file_path = os.path.join(os.path.dirname(__file__), "ai_model_costs.json")
with open(_models_file_path, "r") as f:
    _models_data = json.load(f)

# Convert to AIModel objects
_models: List[AIModel] = [AIModel(**model_data) for model_data in _models_data]

# Create lookup dictionaries for faster access
_models_by_id: Dict[str, AIModel] = {model.id: model for model in _models}
_available_models: List[AIModel] = [model for model in _models if model.available]


def get_all_models() -> List[AIModel]:
    """Get all models, regardless of availability"""
    return _models


def get_available_models() -> List[AIModel]:
    """Get only available models"""
    return _available_models


def get_provider_models(provider: ModelProvider, available_only: bool = True) -> List[AIModel]:
    """Get models from a specific provider"""
    if available_only:
        return [model for model in _available_models if model.provider == provider]
    return [model for model in _models if model.provider == provider]


def get_model_by_id(model_id: str) -> Optional[AIModel]:
    """Get a specific model by ID"""
    return _models_by_id.get(model_id)


def is_model_available(model_id: str) -> bool:
    """Check if a model is available"""
    model = _models_by_id.get(model_id)
    return model is not None and model.available


def estimate_cost_usd(
    model_id: str, 
    input_tokens: int, 
    output_tokens: Optional[int] = None
) -> float:
    """
    Calculate the cost in USD for using a model with the given token counts
    
    Args:
        model_id: ID of the model to use
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (defaults to 0 if not specified)
        
    Returns:
        Estimated cost in USD
        
    Raises:
        ValueError: If the model ID is not recognized
    """
    model = _models_by_id.get(model_id)
    if not model:
        raise ValueError(f"Unknown model ID: {model_id}")
    
    input_cost = (input_tokens / 1000) * model.input_cost_usd_per_1k_tokens
    output_cost = 0
    if output_tokens:
        output_cost = (output_tokens / 1000) * model.output_cost_usd_per_1k_tokens
    
    return input_cost + output_cost


def estimate_credits(model_id: str, input_tokens: int, output_tokens: Optional[int] = None) -> int:
    """
    Calculate the cost in credits for using a model with the given token counts
    1 credit = $0.01 USD
    
    Args:
        model_id: ID of the model to use
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (defaults to 0 if not specified)
        
    Returns:
        Estimated cost in credits (minimum 1)
        
    Raises:
        ValueError: If the model ID is not recognized
    """
    cost_usd = estimate_cost_usd(model_id, input_tokens, output_tokens)
    credits = int(cost_usd * 100)  # Convert to credits (1 credit = $0.01)
    return max(1, credits)  # Minimum 1 credit per operation 