"""
FastAPI Dependencies

Functions to provide dependencies like settings, database sessions, and API clients.
"""

from functools import lru_cache
import openai
import anthropic
from .config.settings import Settings
from fastapi import Depends

@lru_cache()
def get_settings() -> Settings:
    """Returns the application settings instance (cached)."""
    return Settings()

# --- AI Client Dependencies ---

# Cache the clients to avoid re-initialization on every request
_openai_client = None
_anthropic_client = None

def get_openai_client() -> openai.AsyncOpenAI | None:
    """
    Initializes and returns an async OpenAI client if the API key is configured.
    Returns None otherwise.
    Caches the client instance.
    """
    global _openai_client
    if _openai_client is not None:
        return _openai_client

    settings = get_settings()
    api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
    
    if api_key:
        try:
            _openai_client = openai.AsyncOpenAI(api_key=api_key)
            print("OpenAI client initialized.")
            return _openai_client
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            return None
    else:
        print("OpenAI API key not configured. Client not initialized.")
        return None

def get_anthropic_client() -> anthropic.AsyncAnthropic | None:
    """
    Initializes and returns an async Anthropic client if the API key is configured.
    Returns None otherwise.
    Caches the client instance.
    """
    global _anthropic_client
    if _anthropic_client is not None:
        return _anthropic_client

    settings = get_settings()
    api_key = settings.ANTHROPIC_API_KEY.get_secret_value() if settings.ANTHROPIC_API_KEY else None
    
    if api_key:
        try:
            _anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
            print("Anthropic client initialized.")
            return _anthropic_client
        except Exception as e:
            print(f"Error initializing Anthropic client: {e}")
            return None
    else:
        print("Anthropic API key not configured. Client not initialized.")
        return None

# --- Database Dependency (Placeholder - Adapt to your actual setup) ---
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
# from contextlib import asynccontextmanager

# DATABASE_URL = get_settings().DATABASE_URL
# engine = create_async_engine(DATABASE_URL, echo=False)
# AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# async def get_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()

# Mock clients for testing
def get_openai_client_mock():
    """
    Returns an OpenAI client instance.
    For testing, returns a basic client without authentication.
    In production, this would use proper API keys from config.
    """
    # For testing - no actual API calls will be made with mock router
    # In production, you would use:
    # client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    client = openai.AsyncOpenAI(api_key="sk-mock-key-for-testing-only")
    return client

def get_anthropic_client_mock():
    """
    Returns an Anthropic client instance.
    For testing, returns a basic client without authentication.
    In production, this would use proper API keys from config.
    """
    # For testing - no actual API calls will be made with mock router
    # In production, you would use:
    # client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    client = anthropic.AsyncAnthropic(api_key="sk-mock-key-for-testing-only")
    return client 