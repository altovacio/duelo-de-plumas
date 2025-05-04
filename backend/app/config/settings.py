"""
Application Configuration using Pydantic BaseSettings.

Reads settings from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator, BaseModel
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

# Get the directory of the current file (settings.py)
CONFIG_DIR = Path(__file__).parent
AI_COSTS_FILE = CONFIG_DIR / 'ai_model_costs.json'

class AIModelConfig(BaseModel):
    """Configuration for a specific AI model."""
    provider: str = Field(..., description="AI provider (e.g., 'openai', 'anthropic')")
    # Ensure api_name matches the ID used in the JSON for simplicity, or add mapping if needed
    api_name: str = Field(..., description="Model name used in API calls (e.g., 'gpt-4-turbo', 'claude-3-sonnet-20240229')")
    name: str # User-friendly name from JSON
    context_window_k: int # Context window in K tokens
    # Use the specific cost names from the JSON file
    # cost_per_prompt_token: Optional[float] = Field(None, description="Cost in USD per prompt token")
    # cost_per_completion_token: Optional[float] = Field(None, description="Cost in USD per completion token")
    cost_per_1k_prompt_tokens: Optional[float] = Field(None, alias='input_cost_usd_per_1k_tokens', description="Cost in USD per 1000 prompt tokens")
    cost_per_1k_completion_tokens: Optional[float] = Field(None, alias='output_cost_usd_per_1k_tokens', description="Cost in USD per 1000 completion tokens")
    # features: List[str] = Field([], description="List of supported features (e.g., 'generate', 'evaluate')") # REMOVED
    # Add other relevant parameters like context window size if needed
    # context_window: Optional[int] = None
    
    # Allow extra fields from JSON if needed, though strict is better
    # class Config:
    #     extra = 'allow' 

def load_ai_models_from_file(filepath: Path) -> Dict[str, AIModelConfig]:
    """Loads available AI model configurations from the specified JSON file."""
    models_dict = {}
    try:
        with open(filepath, 'r') as f:
            models_data = json.load(f)
            
        if not isinstance(models_data, list):
            print(f"Warning: Expected a list in {filepath}, but got {type(models_data)}. No models loaded.")
            return {}

        for model_info in models_data:
            if isinstance(model_info, dict) and model_info.get('available', False):
                model_id = model_info.get('id')
                if not model_id:
                    print(f"Warning: Skipping model entry due to missing 'id': {model_info}")
                    continue
                
                try:
                    # Map JSON fields to AIModelConfig fields
                    # Use api_name = id from JSON for direct mapping
                    config_data = {
                        'provider': model_info.get('provider', 'unknown').lower(),
                        'api_name': model_id, # Use the model ID as the API name
                        'name': model_info.get('name', model_id),
                        'context_window_k': model_info.get('context_window_k', 0),
                        'input_cost_usd_per_1k_tokens': model_info.get('input_cost_usd_per_1k_tokens'),
                        'output_cost_usd_per_1k_tokens': model_info.get('output_cost_usd_per_1k_tokens')
                    }
                    # Validate and create the config object
                    model_config = AIModelConfig(**config_data)
                    models_dict[model_id] = model_config
                except Exception as e: # Catch Pydantic validation errors or others
                     print(f"Warning: Skipping model '{model_id}' due to config error: {e}. Data: {model_info}")
            # else: skip if not available or not a dictionary
    except FileNotFoundError:
        print(f"Error: AI models file not found at {filepath}. No models loaded.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. No models loaded.")
    except Exception as e:
        print(f"Error loading AI models from {filepath}: {e}. No models loaded.")
        
    if not models_dict:
         print("Warning: No available AI models were loaded from the configuration file.")
         
    return models_dict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'  # Ignore extra fields from environment
    )

    # Application settings
    APP_NAME: str = "Duelo de Plumas v2"
    SECRET_KEY: SecretStr = Field(..., description="Secret key for signing session data, JWTs, etc.")
    DEBUG: bool = False
    # CORS settings (example, adjust as needed)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database settings
    DATABASE_URL: str = Field(..., description="Async database connection string (e.g., postgresql+asyncpg://user:pass@host:port/db)")
    # If using SQLite async: DATABASE_URL="sqlite+aiosqlite:///./v2/app.db"

    # AI Service settings
    OPENAI_API_KEY: SecretStr | None = Field(None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: SecretStr | None = Field(None, description="Anthropic API Key")
    
    # --- AI Model Configuration ---
    # Dictionary mapping user-facing model IDs (used in requests) to their config
    # Loaded from ai_model_costs.json
    AI_MODELS: Dict[str, AIModelConfig] = Field(
        default_factory=lambda: load_ai_models_from_file(AI_COSTS_FILE),
        description="Configuration for available AI models, loaded from ai_model_costs.json"
    )
    # AI_MODELS: Dict[str, AIModelConfig] = Field(default_factory=lambda: {
    #     "gpt-4-turbo": AIModelConfig(
    #         provider="openai",
    #         api_name="gpt-4-turbo",
    #         cost_per_1k_prompt_tokens=0.01,
    #         cost_per_1k_completion_tokens=0.03,
    #         features=["generate", "evaluate"]
    #     ),
    #     "gpt-3.5-turbo": AIModelConfig(
    #         provider="openai",
    #         api_name="gpt-3.5-turbo",
    #         cost_per_1k_prompt_tokens=0.0005,
    #         cost_per_1k_completion_tokens=0.0015,
    #         features=["generate", "evaluate"]
    #     ),
    #     "claude-3-opus": AIModelConfig(
    #         provider="anthropic",
    #         api_name="claude-3-opus-20240229",
    #         cost_per_1k_prompt_tokens=0.015,
    #         cost_per_1k_completion_tokens=0.075,
    #         features=["generate", "evaluate"]
    #     ),
    #      "claude-3-sonnet": AIModelConfig(
    #         provider="anthropic",
    #         api_name="claude-3-sonnet-20240229",
    #         cost_per_1k_prompt_tokens=0.003,
    #         cost_per_1k_completion_tokens=0.015,
    #         features=["generate", "evaluate"]
    #     ),
    #      "claude-3-haiku": AIModelConfig(
    #         provider="anthropic",
    #         api_name="claude-3-haiku-20240307",
    #         cost_per_1k_prompt_tokens=0.00025,
    #         cost_per_1k_completion_tokens=0.00125,
    #         features=["generate", "evaluate"]
    #     ),
    # }, description="Configuration for available AI models")

    # --- Credit System Configuration ---
    CREDITS_PER_DOLLAR: int = Field(100, description="How many credits correspond to 1 USD of AI cost.")
    # Alternative cost model: Credits per token (if not using USD conversion)
    # CREDITS_PER_1K_PROMPT_TOKENS: Optional[int] = Field(None, description="Base credits charged per 1k prompt tokens if USD cost is unavailable.")
    # CREDITS_PER_1K_COMPLETION_TOKENS: Optional[int] = Field(None, description="Base credits charged per 1k completion tokens if USD cost is unavailable.")
    MINIMUM_CREDIT_COST: int = Field(1, description="Minimum credits charged for any successful AI action, even if calculated cost is lower.")
    
    # JWT settings (example, needs implementation)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

# Create a single instance to be imported
settings = Settings() 