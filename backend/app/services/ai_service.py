from typing import Dict, List, Optional, Tuple, Any
import os
import json
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.utils.ai_models import (
    get_model_by_id,
    is_model_available,
    estimate_credits,
    estimate_cost_usd
)
from app.services.ai_provider_service import (
    get_provider_for_model,
    estimate_token_count,
    AIProviderInterface
)
from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Import strategies
from app.services.ai_strategies.writer_strategies import WriterStrategy
from app.services.ai_strategies.judge_strategies import JudgeStrategy
from app.services.ai_strategies.base_strategy import WriterStrategyInterface, JudgeStrategyInterface

# This is a placeholder for actual LLM integration
# In a real implementation, you would use a library like openai for GPT models
class AIService:
    """Service for interacting with LLM models using a strategy pattern."""
    
    @classmethod
    def validate_model(cls, model: str) -> None:
        """Validate that the requested model is available."""
        if not is_model_available(model):
            # Get list of available models for error message
            from app.utils.ai_models import get_available_models
            available_models = [m.id for m in get_available_models()]
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not available or not enabled. Available models: {available_models}"
            )
            
    @classmethod
    def estimate_token_count(cls, text: str, model_id: str) -> int:
        """
        Estimate the number of tokens in a text.
        This now passes the model_id to the underlying provider-specific estimator.
        """
        return estimate_token_count(text, model_id=model_id)
        
    @staticmethod
    def _get_provider(model_id: str) -> AIProviderInterface:
        """Retrieves and instantiates the appropriate AI provider class for the given model_id."""
        # Directly use the get_provider_for_model function from ai_provider_service
        provider_class = get_provider_for_model(model_id)
        
        if not provider_class:
            logger.error(f"No provider CLASS found for model '{model_id}' by get_provider_for_model.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Changed to 500 as this indicates a configuration/mapping issue
                detail=f"No provider implementation class could be determined for model '{model_id}'. Check model configuration and provider mapping."
            )
        return provider_class() # Instantiates the provider (e.g., OpenAIProvider())

    @classmethod
    async def generate_text(
        cls, 
        model: str, 
        personality_prompt: str,
        user_guidance_title: Optional[str] = None,
        user_guidance_description: Optional[str] = None,
        contest_description: Optional[str] = None,
        temperature: Optional[float] = None, 
        max_tokens: Optional[int] = None,
        strategy_name: str = "default",
        # Debug logging parameters (optional)
        db_session=None,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None
    ) -> Tuple[str, int, int]:
        
        provider = cls._get_provider(model)
        
        # Strategy selection for future extensibility
        writer_strategy: WriterStrategyInterface
        if strategy_name == "default" or strategy_name == "structured":
            writer_strategy = WriterStrategy()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown writer strategy: {strategy_name}. Available strategies: default, structured"
            )

        # Determine actual parameters to use, falling back to config defaults
        actual_temperature = temperature if temperature is not None else settings.DEFAULT_WRITER_TEMPERATURE
        actual_max_tokens = max_tokens if max_tokens is not None else settings.DEFAULT_WRITER_MAX_TOKENS

        try:
            generated_content, prompt_tokens, completion_tokens = await writer_strategy.generate(
                provider=provider,
                model_id=model,
                personality_prompt=personality_prompt,
                contest_description=contest_description,
                user_guidance_title=user_guidance_title,
                user_guidance_description=user_guidance_description,
                temperature=actual_temperature, 
                max_tokens=actual_max_tokens,
                # Pass debug logging parameters
                db_session=db_session,
                user_id=user_id,
                agent_id=agent_id
            )
            
            return generated_content, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"Error in AIService.generate_text with strategy {strategy_name}: {str(e)}")
            # Re-raise or handle more gracefully if the exception is from the provider vs strategy
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating text via {strategy_name}: {str(e)}"
            )

    @classmethod
    async def judge_contest(
        cls,
        model: str,
        personality_prompt: str,
        contest_description: str,
        texts: List[Dict[str, Any]],
        temperature: Optional[float] = None, 
        max_tokens: Optional[int] = None,    
        strategy_name: str = "default",
        # Debug logging parameters (optional)
        db_session=None,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        contest_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        
        provider = cls._get_provider(model)

        judge_strategy: JudgeStrategyInterface
        if strategy_name == "default" or strategy_name == "structured":
            judge_strategy = JudgeStrategy()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown judge strategy: {strategy_name}. Available strategies: default, structured"
            )
        
        # Determine actual parameters to use, falling back to config defaults
        actual_temperature = temperature if temperature is not None else settings.DEFAULT_JUDGE_TEMPERATURE
        actual_max_tokens = max_tokens if max_tokens is not None else settings.DEFAULT_JUDGE_MAX_TOKENS

        try:
            # Strategy now handles its default temperature/max_tokens if these are None
            parsed_votes, prompt_tokens, completion_tokens = await judge_strategy.judge(
                provider=provider,
                model_id=model,
                personality_prompt=personality_prompt,
                contest_description=contest_description,
                texts=texts,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens,
                # Pass debug logging parameters
                db_session=db_session,
                user_id=user_id,
                agent_id=agent_id,
                contest_id=contest_id
            )

            total_tokens = prompt_tokens + completion_tokens
            # model_info = get_model_by_id(model) # No longer needed here
            # avg_cost_per_1k = 0.0 # Removed
            # if model_info and total_tokens > 0: # Removed
            #     avg_cost_per_1k = ( # Removed
            #         model_info.input_cost_usd_per_1k_tokens * prompt_tokens + # Removed
            #         model_info.output_cost_usd_per_1k_tokens * completion_tokens # Removed
            #     ) / total_tokens * 1000 # Removed
            
            # Return prompt and completion tokens separately for accurate cost calculation later
            return parsed_votes, prompt_tokens, completion_tokens # Changed return value
        except Exception as e:
            logger.error(f"Error in AIService.judge_contest with strategy {strategy_name}: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error judging contest via {strategy_name}: {str(e)}"
            )

    @classmethod
    def estimate_tokens_for_judging(
        cls, 
        model: str, 
        prompt_length: int, 
        contest_desc_length: int, 
        texts: List[Dict]
    ) -> int:
        """
        Estimate the number of tokens that will be used for judging a contest.
        This is a rough estimate based on the length of the prompt, contest description, and texts.
        """
        # Estimate tokens for texts
        text_tokens = 0
        for text in texts:
            # Title plus content plus some overhead
            text_tokens += estimate_token_count(text.get('title', ''), model_id=model) + estimate_token_count(text.get('content', ''), model_id=model) + 50
        
        # Estimate for individual evaluations
        eval_tokens = text_tokens * 2  # Roughly double the text size for evaluations
        
        # Estimate for final ranking
        # Base prompt + contest description + some text for each evaluation
        ranking_tokens = contest_desc_length + 200 + (len(texts) * 100)
        
        # System message tokens
        system_tokens = 100
        
        # Total estimate
        total_tokens = prompt_length + contest_desc_length + text_tokens + eval_tokens + ranking_tokens + system_tokens
        
        # Add a buffer for safety
        return int(total_tokens * 1.2)  # 20% buffer 