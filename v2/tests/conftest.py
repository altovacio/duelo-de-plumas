"""
Configuration for pytest.
"""
import sys
import os
from pathlib import Path

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path so we can import from app modules
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure we can import from v2
if str(Path("v2")) not in sys.path:
     sys.path.insert(0, str(Path("v2")))
     
# Must import AFTER path modification
from v2.main import app # Your FastAPI app instance
from v2.database import Base, get_db_session # Import Base for metadata
from v2.fastapi_config import settings as app_settings # Import your app settings
from v2 import models # To create test data

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db.sqlite"

# Override database URL setting for testing
# Note: This assumes your get_db_session dependency uses settings.DATABASE_URL implicitly or explicitly
# If get_db_session hardcodes the URL, this override won't work directly on the dependency
# A better approach is often to override the get_db_session dependency itself (see below)
# For now, let's assume settings are used or we override the dependency
app_settings.DATABASE_URL = TEST_DATABASE_URL 

# Create async engine and session factory for the test database
engine = create_async_engine(TEST_DATABASE_URL, echo=False) # Turn echo=True for SQL debugging
TestingSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Creates tables before each test function and drops them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Optionally delete the test db file if not in-memory
    # if os.path.exists("./test_db.sqlite"): 
    #     os.remove("./test_db.sqlite")

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields a database session for a test function."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback() # Rollback changes after test

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Creates an HTTP client for testing the API."""
    
    # Dependency override for the database session
    def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    
    # Use ASGITransport for the app argument
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    
    # Clean up dependency override after test
    app.dependency_overrides.pop(get_db_session, None)

# --- Test Data Fixtures --- 

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> models.User:
    """Creates a regular test user."""
    user = models.User(
        username="testuser",
        email="test@example.com",
        role="judge", # or 'user' depending on default role
        judge_type="human"
    )
    user.set_password("password") # Use the bcrypt method from the model
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> models.User:
    """Creates an admin test user."""
    user = models.User(
        username="adminuser",
        email="admin@example.com",
        role="admin",
        judge_type="human"
    )
    user.set_password("adminpassword")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user 

# --- Logged-in Client Fixtures --- 

# NOTE: We need separate client instances for different logged-in users 
# to avoid header conflicts if tests run concurrently or fixtures are reused unexpectedly.

@pytest_asyncio.fixture(scope="function")
async def base_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides a base AsyncClient with dependency overrides, but no auth headers."""
    def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.pop(get_db_session, None)


@pytest_asyncio.fixture(scope="function")
async def logged_in_client(base_client: AsyncClient, test_user: models.User) -> AsyncClient:
    """Logs in the regular test_user using the base client."""
    base_client.headers.pop("Authorization", None)
    login_data = {"username": test_user.username, "password": "password"}
    login_response = await base_client.post("/auth/token", data=login_data)
    assert login_response.status_code == 200, f"Failed to log in test_user: {login_response.text}"
    token = login_response.json()["access_token"]
    base_client.headers["Authorization"] = f"Bearer {token}"
    return base_client # Return the same client instance with headers set

@pytest_asyncio.fixture(scope="function")
async def admin_token(base_client: AsyncClient, admin_user: models.User) -> str:
    """Logs in the admin user using the base_client and returns their access token."""
    # Use the base_client provided by fixture dependency
    base_client.headers.pop("Authorization", None) # Ensure clean state
    login_data = {"username": admin_user.username, "password": "adminpassword"}
    login_response = await base_client.post("/auth/token", data=login_data)
    assert login_response.status_code == 200, f"Failed to log in admin_user for token: {login_response.text}"
    token = login_response.json()["access_token"]
    # Don't set header here, just return the token
    base_client.headers.pop("Authorization", None) # Clean up header if login set it
    return token

# REMOVED old admin_logged_in_client fixture
# @pytest_asyncio.fixture(scope="function")
# async def admin_logged_in_client(...) -> AsyncGenerator[AsyncClient, None]: ... 