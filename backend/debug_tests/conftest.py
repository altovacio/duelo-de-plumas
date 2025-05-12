import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# --- Alembic and SQLAlchemy specific imports ---
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from sqlalchemy import text # For raw SQL execution if needed

# --- Path Setup ---
# Assumes conftest.py is in backend/debug_tests/, and backend root (/app in Docker) is its parent.
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- Settings Override (CRUCIAL: Must happen before other app imports) ---
try:
    from app.core.config import settings
    if settings.DATABASE_URL_TEST:
        print(f"INFO [debug_tests/conftest.py]: Overriding DATABASE_URL with DATABASE_URL_TEST: {settings.DATABASE_URL_TEST}")
        settings.DATABASE_URL = settings.DATABASE_URL_TEST # This should be the one the engine uses
    else:
        # If not set, tests might run on the main DB or fail. Add a strong warning or fail.
        pytest.fail("CRITICAL [debug_tests/conftest.py]: DATABASE_URL_TEST not set. Tests must run on a dedicated test database.")
except ImportError as e:
    pytest.fail(f"CRITICAL [debug_tests/conftest.py]: Failed to import 'settings' from 'app.core.config'. Error: {e}")
except AttributeError as e:
    pytest.fail(f"CRITICAL [debug_tests/conftest.py]: 'DATABASE_URL_TEST' not found in settings. Ensure it is defined. Error: {e}")

# --- App Component Imports (after settings override) ---
try:
    from app.main import app  # Your FastAPI application
    from app.db.database import Base, get_db as original_get_db # Import original get_db for override
    from scripts.create_admin import create_admin_user
except ImportError as e:
    app = None
    Base = None
    create_admin_user = None
    original_get_db = None
    pytest.fail(f"CRITICAL [debug_tests/conftest.py]: Failed to import essential app components. Error: {e}")

TestAsyncSessionLocal = None # Will be initialized in setup_debug_database

@pytest.fixture(scope="session", autouse=True)
async def setup_debug_database():
    global TestAsyncSessionLocal, app # Allow modification of global app for dependency override

    print("INFO [debug_tests/conftest.py]: Starting session-scoped database setup.")
    
    if not settings.DATABASE_URL_TEST:
        pytest.fail("CRITICAL [debug_tests/conftest.py]: DATABASE_URL_TEST is not set.")

    # Create a new engine specifically for this test session, using NullPool
    test_engine = create_async_engine(
        settings.DATABASE_URL_TEST, 
        echo=settings.DEBUG, 
        poolclass=NullPool
    )
    TestAsyncSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    print(f"DEBUG [debug_tests/conftest.py]: Test engine created with URL: {test_engine.url} using NullPool")

    # Alembic setup using the test_engine's URL (which is settings.DATABASE_URL_TEST)
    alembic_ini_path = "alembic.ini"
    if not os.path.exists(alembic_ini_path):
        pytest.fail(f"CRITICAL [debug_tests/conftest.py]: Alembic config ('{alembic_ini_path}') not found.")

    alembic_cfg = AlembicConfig(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", str(test_engine.url))

    print(f"INFO [debug_tests/conftest.py]: Applying Alembic migrations to: {test_engine.url}")
    try:
        print("INFO [debug_tests/conftest.py]: Downgrading test database to 'base'...")
        alembic_command.downgrade(alembic_cfg, "base")
        print("INFO [debug_tests/conftest.py]: Upgrading test database to 'head'...")
        alembic_command.upgrade(alembic_cfg, "head")
        print("INFO [debug_tests/conftest.py]: Alembic migrations applied successfully.")
    except Exception as e:
        pytest.fail(f"CRITICAL [debug_tests/conftest.py]: Alembic migration process failed. Error: {e}")

    # Override app dependency for get_db
    async def get_test_db_session():
        async with TestAsyncSessionLocal() as session:
            yield session

    if app and original_get_db: # Ensure app and original_get_db were imported
        app.dependency_overrides[original_get_db] = get_test_db_session
        print("INFO [debug_tests/conftest.py]: FastAPI app's get_db dependency overridden.")
    else:
        pytest.fail("CRITICAL [debug_tests/conftest.py]: FastAPI 'app' or original 'get_db' not available for override.")

    print(f"INFO [debug_tests/conftest.py]: Creating admin user: {settings.FIRST_SUPERUSER_USERNAME}")
    try:
        # Use TestAsyncSessionLocal for creating admin user
        async with TestAsyncSessionLocal() as temp_admin_db_session:
            await create_admin_user( # create_admin_user now accepts a session
                db=temp_admin_db_session, 
                username=settings.FIRST_SUPERUSER_USERNAME,
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD
            )
        
        # Verify admin creation using a new session from TestAsyncSessionLocal
        async with TestAsyncSessionLocal() as temp_db_verify:
            from app.services.auth_service import get_user_by_username
            admin = await get_user_by_username(temp_db_verify, settings.FIRST_SUPERUSER_USERNAME)
            if not admin or not admin.is_admin:
                pytest.fail("CRITICAL [debug_tests/conftest.py]: Admin user not found or not admin after create_admin_user call.")
        print("INFO [debug_tests/conftest.py]: Admin user created and verified successfully.")
    
    except Exception as e:
        pytest.fail(f"CRITICAL [debug_tests/conftest.py]: Failed during admin user creation/verification. Error: {e}")

    yield # Tests run here

    print("INFO [debug_tests/conftest.py]: Starting session-scoped database teardown.")
    try:
        print(f"INFO [debug_tests/conftest.py]: Downgrading test database '{test_engine.url}' to 'base' for cleanup...")
        alembic_command.downgrade(alembic_cfg, "base") # uses sync wrapper
        print("INFO [debug_tests/conftest.py]: Test database downgraded successfully.")
    except Exception as e:
        print(f"WARNING [debug_tests/conftest.py]: Failed to downgrade test database. Error: {e}")
    
    await test_engine.dispose() # Dispose of the test-specific engine
    print("INFO [debug_tests/conftest.py]: Test engine disposed.")

@pytest.fixture(scope="function")
async def db_session(setup_debug_database) -> AsyncSession:
    if not TestAsyncSessionLocal:
        pytest.fail("CRITICAL [debug_tests/conftest.py]: 'TestAsyncSessionLocal' is not initialized.")
    async with TestAsyncSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def client(setup_debug_database, db_session: AsyncSession) -> AsyncClient:
    if not app:
        pytest.fail("CRITICAL [debug_tests/conftest.py]: FastAPI 'app' is not available.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# TODO: Add database setup/teardown logic (Alembic migrations, admin user creation)
# similar to the main conftest.py's setup_database_suite fixture.
# This will likely need to be a session-scoped autouse fixture.
# For now, the tests might run against whatever state the DB is in if not reset. 