import tiktoken
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ... import models
from ..config.settings import Settings, AIModelConfig
# Assuming get_settings is a dependency that provides the Settings instance
# If settings are globally available or passed differently, adjust accordingly
from ..dependencies import get_settings

# --- Helper Functions (moved from ai_service) ---

def get_model_config(model_id: str, settings: Settings) -> Optional[AIModelConfig]:
    """Retrieves the configuration for a specific model_id from settings."""
    return settings.AI_MODELS.get(model_id)

def count_tokens(text: str, model_id: str, settings: Settings) -> int:
    """
    Calculates the token count for the given text based on the model.
    Uses tiktoken with fallbacks for models not directly supported by tiktoken.
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        try:
            encoding = tiktoken.get_encoding("cl100k_base") # Common default
            return len(encoding.encode(text))
        except Exception:
            return len(text.split()) # Very rough fallback: word count

    encoding_name = "cl100k_base" # Default for newer OpenAI models
    if model_config.provider == "openai":
        if "gpt-3.5" in model_config.api_name or "gpt-4" in model_config.api_name:
            encoding_name = "cl100k_base"
    # Add other provider/model specific encoding names if necessary

    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print(f"Error getting tiktoken encoding {encoding_name} for model {model_id}: {e}. Falling back.")
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text.split()) # Final fallback

def calculate_monetary_cost(model_id: str, prompt_tokens: int, completion_tokens: int, settings: Settings) -> Optional[float]:
    """
    Calculates the estimated monetary cost (e.g., in USD) based on token counts
    and pricing information from settings. Returns None if cost cannot be determined.
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        return None

    cost = 0.0
    calculated = False

    if model_config.cost_per_1k_prompt_tokens is not None and model_config.cost_per_1k_completion_tokens is not None:
        cost += (prompt_tokens / 1000) * model_config.cost_per_1k_prompt_tokens
        cost += (completion_tokens / 1000) * model_config.cost_per_1k_completion_tokens
        calculated = True
    elif model_config.cost_per_prompt_token is not None and model_config.cost_per_completion_token is not None:
        cost += prompt_tokens * model_config.cost_per_prompt_token
        cost += completion_tokens * model_config.cost_per_completion_token
        calculated = True

    return cost if calculated else None

def calculate_credit_cost(
    model_id: str, # Added model_id to fetch its config for potential direct token-to-credit rates
    prompt_tokens: int,
    completion_tokens: int,
    settings: Settings
) -> int:
    """
    Translates monetary cost and/or token counts into the integer credit cost.
    Prioritizes monetary cost conversion if available, otherwise direct token-to-credit.
    """
    monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)
    credit_cost = 0

    if monetary_cost is not None and settings.CREDITS_PER_DOLLAR > 0:
        credit_cost = int(monetary_cost * settings.CREDITS_PER_DOLLAR)
    else:
        # Fallback or alternative: direct token-to-credit calculation if defined
        model_config = get_model_config(model_id, settings)
        if model_config:
            if model_config.credits_per_1k_prompt_tokens is not None and \
               model_config.credits_per_1k_completion_tokens is not None:
                credit_cost += int((prompt_tokens / 1000) * model_config.credits_per_1k_prompt_tokens)
                credit_cost += int((completion_tokens / 1000) * model_config.credits_per_1k_completion_tokens)
            elif model_config.credits_per_prompt_token is not None and \
                 model_config.credits_per_completion_token is not None:
                credit_cost += int(prompt_tokens * model_config.credits_per_prompt_token)
                credit_cost += int(completion_tokens * model_config.credits_per_completion_token)

    # Add a safety margin to the credit cost
    credit_cost *= 1.5 
    
    final_cost = max(settings.MINIMUM_CREDIT_COST, credit_cost)
    return max(0, final_cost) # Ensure non-negative

async def record_credit_transaction_and_update_user(
    db: AsyncSession,
    user_id: int,
    credits_change: int, # Negative for debit, positive for credit
    action_type: str,
    settings: Settings, # Pass settings for MINIMUM_CREDIT_COST and other configs if needed for ledger logic
    description: Optional[str] = None,
    real_cost: Optional[float] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None # For storing extra details like token counts
) -> models.CostLedger:
    """
    Records a credit transaction in the CostLedger and updates the user's credit balance.
    Raises HTTPException if the user has insufficient credits for a debit.
    'credits_change' should be negative for debits.
    """
    user = await db.get(models.User, user_id)
    if not user:
        # This case should ideally be caught earlier (e.g., by auth dependencies)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for credit transaction.")

    if credits_change < 0: # It's a debit
        if user.credits < abs(credits_change):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED, # Or 400 Bad Request
                detail=f"Insufficient credits. Current balance: {user.credits}, required: {abs(credits_change)}."
            )

    # Update user's credit balance
    user.credits += credits_change
    new_balance = user.credits
    
    # Create CostLedger entry
    ledger_entry = models.CostLedger(
        user_id=user_id,
        action_type=action_type,
        credits_change=credits_change,
        real_cost=real_cost,
        description=description,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        resulting_balance=new_balance,
        # metadata=metadata # metadata field is not in CostLedger model as per previous file. Add if needed.
                          # If metadata is to be stored, consider adding a JSON field to CostLedger.
                          # For now, relevant details can go into 'description'.
    )
    
    db.add(user) # Add user to session for credit update
    db.add(ledger_entry)
    
    # The caller (e.g., router endpoint) should handle the session.commit()
    # await db.commit() # Avoid committing here to allow atomicity with other operations
    # await db.refresh(ledger_entry)
    # await db.refresh(user)
    
    return ledger_entry 