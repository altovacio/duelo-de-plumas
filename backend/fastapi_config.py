import os
from pydantic import Field, EmailStr, PostgresDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union

# Determine the base directory of the project (where .env might be)
# Adjust the number of .parent calls if your config file is nested deeper
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # Core App Settings
    APP_NAME: str = "Duelo de Plumas API"
    APP_VERSION: str = "2.0"
    DEBUG: bool = Field(False, description="Enable debug mode")
    SECRET_KEY: str = Field(..., description="Secret key for signing tokens, etc.") # Required
    ALLOWED_HOSTS: List[str] = Field(["*"], description="Allowed hosts for the server") # Default to all for development

    # Database Settings (Async PostgreSQL Example)
    # For SQLite async: DATABASE_URL="sqlite+aiosqlite:///./fastapi_app.db"
    DATABASE_URL: Union[PostgresDsn, str] = Field(..., description="Async database connection string") # Required

    # Authentication Settings (JWT)
    AUTH_ALGORITHM: str = Field("HS256", description="Algorithm for JWT signing")
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Access token expiry time in minutes")

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(None, description="API Key for OpenAI")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="API Key for Anthropic")

    # Other settings from original config if needed
    LANGUAGES: List[str] = Field(['es'], description="Supported languages")

    # Example contest parameters (can be moved to DB or kept here)
    # MAX_SUBMISSION_LENGTH: int = 5000
    # JUDGES_PER_CONTEST: int = 3

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        # Load settings from a .env file located in the project's base directory
        env_file=os.path.join(BASE_DIR, '.env'),
        env_file_encoding='utf-8',
        # Allow extra fields not defined in the model (can be useful)
        extra='ignore'
    )

    # Example validator (can add more as needed)
    @validator("DATABASE_URL", pre=True, allow_reuse=True)
    def check_db_url(cls, value):
        if isinstance(value, str) and value.startswith("postgres://"):
            # If using standard postgres://, replace with postgresql:// for SQLAlchemy compatibility
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if isinstance(value, str) and value.startswith("sqlite://"):
             # If using standard sqlite://, replace with sqlite+aiosqlite:// for async
             return value.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return value

    # ADDED: Expiry for temporary contest access tokens (via password check)
    CONTEST_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(15, description="Contest access token expiry time in minutes")

    # Add SECURE_COOKIES setting for production
    SECURE_COOKIES: bool = Field(False, description="Set to True when using HTTPS")


# Create a single instance of the settings to be imported elsewhere
settings = Settings()

# Example usage (can be removed later):
if __name__ == "__main__":
    print("Loaded Settings:")
    print(f"  App Name: {settings.APP_NAME}")
    print(f"  Debug Mode: {settings.DEBUG}")
    print(f"  Database URL: {settings.DATABASE_URL}")
    print(f"  OpenAI Key Set: {'Yes' if settings.OPENAI_API_KEY else 'No'}")
    print(f"  Anthropic Key Set: {'Yes' if settings.ANTHROPIC_API_KEY else 'No'}")
    print(f"  Base Dir: {BASE_DIR}")
    print(f"  Env file path: {os.path.join(BASE_DIR, '.env')}")

    # Example check for required fields
    if not settings.SECRET_KEY:
        print("\nERROR: SECRET_KEY is not set in environment or .env file!")
    if not settings.DATABASE_URL:
        print("\nERROR: DATABASE_URL is not set in environment or .env file!") 