# backend/tests/conftest.py
import sys
import os
from pathlib import Path
import pytest
import asyncio
import uuid

# --- SQLAlchemy & HTTPX specific imports ---
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport # For the new client fixture

# --- Path Setup ---
# Ensures tests can find the 'app' module.
# Assumes conftest.py is in backend/tests/, and backend root (/app in Docker) is its parent.
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- Settings Override (CRUCIAL: Must happen before other app imports that initialize DB engine) ---
try:
    from app.core.config import settings
    if settings.DATABASE_URL_TEST:
        print(f"INFO [conftest.py]: Overriding DATABASE_URL with DATABASE_URL_TEST: {settings.DATABASE_URL_TEST}")
        settings.DATABASE_URL = settings.DATABASE_URL_TEST
        # Note: If app.db.database.engine is initialized at import time (common),
        # this override must occur before app.db.database is imported anywhere.
        # If issues persist where the main DB URL is still used by the engine,
        # a re-initialization mechanism for the engine/SessionLocal in app.db.database
        # callable from here would be more robust.
    else:
        # To require a test database and prevent accidental runs on the main DB:
        # pytest.fail("CRITICAL: DATABASE_URL_TEST not set. Tests must run on a dedicated test database.")
        print("WARNING [conftest.py]: DATABASE_URL_TEST not set. Tests will attempt to run on DATABASE_URL. THIS IS NOT RECOMMENDED AND MAY FAIL OR CAUSE DATA LOSS.")
except ImportError as e:
    pytest.fail(f"CRITICAL [conftest.py]: Failed to import 'settings' from 'app.core.config'. Base settings are unavailable. Error: {e}")
except AttributeError as e:
    # This might happen if DATABASE_URL_TEST is not an attribute of settings object
    pytest.fail(f"CRITICAL [conftest.py]: 'DATABASE_URL_TEST' not found in settings. Ensure it is defined in app.core.config.Settings. Error: {e}")


# --- Alembic and SQLAlchemy Imports (after settings override) ---
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

# --- App Component Imports (these will now use the overridden settings.DATABASE_URL) ---
try:
    from app.main import app
    from app.db.database import Base, get_db as original_get_db # Import Base and original get_db
    from scripts.create_admin import create_admin_user
except ImportError as e:
    # Nullify to allow fixtures to detect and fail gracefully
    app = None
    Base = None
    original_get_db = None
    create_admin_user = None
    pytest.fail(f"CRITICAL [conftest.py]: Failed to import essential app components (app, DB essentials, create_admin_user). Error: {e}")

# Global for test-specific session factory, initialized in setup_database_suite
TestAsyncSessionLocal = None

# --- Fixtures ---

@pytest.fixture(scope="session", autouse=True)
async def setup_database_suite():
    global TestAsyncSessionLocal, app # Allow modification

    print("INFO [conftest.py]: Starting session-scoped database setup (Main Tests).")
    
    if not settings.DATABASE_URL_TEST: # Should be redundant due to earlier check, but good for safety
        pytest.fail("CRITICAL [conftest.py]: DATABASE_URL_TEST is not set in setup_database_suite.")

    if not all([Base, create_admin_user, app, original_get_db]):
         pytest.fail("CRITICAL [conftest.py]: Essential app components (Base, create_admin_user, app, original_get_db) are missing.")

    # Create a new engine specifically for this test session using NullPool
    test_engine = create_async_engine(
        settings.DATABASE_URL_TEST,
        echo=settings.DEBUG, # Or False for less verbose logs
        poolclass=NullPool
    )
    TestAsyncSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    print(f"DEBUG [conftest.py]: Test engine created with URL: {test_engine.url} using NullPool (Main Tests)")

    # Alembic setup using the test_engine's URL
    alembic_ini_path = "alembic.ini"
    if not os.path.exists(alembic_ini_path):
        pytest.fail(f"CRITICAL [conftest.py]: Alembic config ('{alembic_ini_path}') not found.")

    alembic_cfg = AlembicConfig(alembic_ini_path)
    # settings.DATABASE_URL is already DATABASE_URL_TEST due to override
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL)) 

    print(f"INFO [conftest.py]: Applying Alembic migrations to: {settings.DATABASE_URL} (Main Tests)")
    try:
        print("INFO [conftest.py]: Downgrading test database to 'base' (Main Tests)...")
        alembic_command.downgrade(alembic_cfg, "base")
        print("INFO [conftest.py]: Upgrading test database to 'head' (Main Tests)...")
        alembic_command.upgrade(alembic_cfg, "head")
        print("INFO [conftest.py]: Alembic migrations applied successfully (Main Tests).")
    except Exception as e:
        pytest.fail(f"CRITICAL [conftest.py]: Alembic migration process failed. Error: {e} (Main Tests)")

    # Override app dependency for get_db
    async def get_test_db_session():
        if not TestAsyncSessionLocal:
             pytest.fail("CRITICAL [conftest.py]: TestAsyncSessionLocal not initialized before get_test_db_session call.")
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[original_get_db] = get_test_db_session
    print("INFO [conftest.py]: FastAPI app's get_db dependency overridden (Main Tests).")

    # Create admin user using the new TestAsyncSessionLocal
    print(f"INFO [conftest.py]: Creating admin user: {settings.FIRST_SUPERUSER_USERNAME} (Main Tests)")
    try:
        async with TestAsyncSessionLocal() as temp_admin_db_session:
            await create_admin_user( # create_admin_user now accepts a session
                db=temp_admin_db_session, 
                username=settings.FIRST_SUPERUSER_USERNAME,
                email=settings.FIRST_SUPERUSER_EMAIL,
                password=settings.FIRST_SUPERUSER_PASSWORD
            )
        # Verification
        async with TestAsyncSessionLocal() as temp_db_verify:
            from app.db.repositories.user_repository import UserRepository # Import UserRepository
            user_repo = UserRepository(temp_db_verify) # Instantiate repository
            admin = await user_repo.get_by_username(settings.FIRST_SUPERUSER_USERNAME) # Use repository
            if not admin or not admin.is_admin:
                pytest.fail(f"CRITICAL [conftest.py]: Admin user '{settings.FIRST_SUPERUSER_USERNAME}' NOT found or not admin after creation (Main Tests).")
        print(f"INFO [conftest.py]: Admin user '{settings.FIRST_SUPERUSER_USERNAME}' created and verified successfully (Main Tests).")
    except Exception as e:
        pytest.fail(f"CRITICAL [conftest.py]: Failed during admin user creation/verification. Error: {e} (Main Tests)")
    
    print("--- [conftest.py] Test Suite Database Setup Complete (Main Tests) ---")
    
    yield # Tests run here
    
    print("--- [conftest.py] Initiating Test Suite Teardown (Main Tests) ---")
    try:
        print(f"INFO [conftest.py]: Downgrading test database '{settings.DATABASE_URL}' to 'base' for cleanup (Main Tests)...")
        alembic_command.downgrade(alembic_cfg, "base")
        print("INFO [conftest.py]: Test database successfully downgraded (Main Tests).")
    except Exception as e:
        print(f"WARNING [conftest.py]: Failed to downgrade test database during teardown. Error: {e} (Main Tests)")
    
    await test_engine.dispose() 
    print("INFO [conftest.py]: Test engine disposed (Main Tests).")

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient: # Ensure db_session is a dependency to respect setup order
    """Provides an httpx.AsyncClient instance for API testing."""
    if not app:
        pytest.fail("CRITICAL [conftest.py]: FastAPI 'app' is not available. Cannot create AsyncClient.")
    
    # Ensure setup_database_suite has run and TestAsyncSessionLocal is ready,
    # and dependency_overrides are set. db_session fixture implicitly depends on setup_database_suite.
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        follow_redirects=False
    ) as ac:
        yield ac

@pytest.fixture(scope="function")
async def db_session() -> AsyncSession: # No longer needs setup_database_suite as explicit dep, autouse=True handles it
    """Provides a clean, async database session from TestAsyncSessionLocal for each test function."""
    if not TestAsyncSessionLocal:
        pytest.fail("CRITICAL [conftest.py]: 'TestAsyncSessionLocal' is not initialized for db_session.")
        
    async with TestAsyncSessionLocal() as session:
        try:
            # Optional: debug print to confirm session details
            # if session.bind:
            #     print(f"DEBUG [conftest.py db_session]: Yielding session {id(session)} bound to URL: {session.bind.url} (Main Tests)")
            yield session
        finally:
            await session.close() # Important for NullPool to actually close connection

# --- Helper Functions (as previously defined) ---
def generate_unique_username(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}_test"

def generate_unique_email(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}@test.plumas.top"

# For the database connectivity check, we need `text` from sqlalchemy
from sqlalchemy import text 