from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv
import json

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Application version
    VERSION: str = "3.0.0"  # Central location for version tracking
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./duelo_de_plumas.db")
    DATABASE_URL_TEST: str | None = os.getenv("DATABASE_URL_TEST") # For test environment
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure_key_for_dev")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # AI API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # App settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:8000"] # Pydantic will parse from JSON env var if present

    # Superuser Credentials (for initial setup/tests)
    # These should align with the credentials used by scripts/create_admin.py
    # and be present in the .env file for the testing environment.
    FIRST_SUPERUSER_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "supersecretpassword") # Ensure .env provides this
    FIRST_SUPERUSER_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")

    # AI Service Defaults
    DEFAULT_WRITER_TEMPERATURE: float = 0.7
    DEFAULT_JUDGE_TEMPERATURE: float = 0.3
    DEFAULT_WRITER_MAX_TOKENS: Optional[int] = 4096
    DEFAULT_JUDGE_MAX_TOKENS: Optional[int] = 4096
    DEFAULT_TEST_MODEL_ID: str = "gpt-4.1-nano-2025-04-14" # Default model for testing

settings = Settings() 