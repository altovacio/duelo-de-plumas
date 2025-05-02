"""
Application Configuration using Pydantic BaseSettings.

Reads settings from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

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
    
    # JWT settings (example, needs implementation)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

# Create a single instance to be imported
settings = Settings() 