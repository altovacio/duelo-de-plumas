# backend/tests/conftest.py
import sys
import os
from pathlib import Path
import pytest
import asyncio
import uuid

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
    from app.db.database import AsyncSessionLocal, Base, engine as async_app_engine # Engine should now use the test DB URL
    from scripts.create_admin import create_admin_user
    # For debugging, print the URL the engine is actually using:
    print(f"DEBUG [conftest.py]: SQLAlchemy Async Engine is configured with URL: {async_app_engine.url}")
    if settings.DATABASE_URL_TEST and str(async_app_engine.url) != settings.DATABASE_URL_TEST:
        print(f"WARNING [conftest.py]: Engine URL {async_app_engine.url} does NOT match DATABASE_URL_TEST {settings.DATABASE_URL_TEST}. Override might not have worked as expected for engine initialization.")

except ImportError as e:
    # Nullify to allow fixtures to detect and fail gracefully
    app = None
    AsyncSessionLocal = None
    Base = None 
    async_app_engine = None
    create_admin_user = None
    pytest.fail(f"CRITICAL [conftest.py]: Failed to import essential app components (app, DB essentials, create_admin_user). Error: {e}")


# --- Fixtures ---

@pytest.fixture(scope="session", autouse=True)
async def setup_database_suite():
    print("INFO [conftest.py]: TOP OF setup_database_suite REACHED (NO event_loop arg - relying on pytest-asyncio)")

    # --- Restore the ACTUAL database setup logic ---
    if not settings.DATABASE_URL_TEST:
        pytest.fail("CRITICAL [conftest.py]: DATABASE_URL_TEST is not set or was not used. Aborting test database setup.")

    if not all([AsyncSessionLocal, Base, async_app_engine, create_admin_user, app]):
         pytest.fail("CRITICAL [conftest.py]: Essential app components are missing. Cannot set up test suite database.")

    alembic_ini_path = "alembic.ini"
    if not os.path.exists(alembic_ini_path):
        pytest.fail(f"CRITICAL [conftest.py]: Alembic config file ('{alembic_ini_path}') not found. CWD: {os.getcwd()}. Pytest rootdir is usually /app in the container.")

    print(f"INFO [conftest.py]: Using Alembic config: '{alembic_ini_path}' with Database URL: {settings.DATABASE_URL}")
    alembic_cfg = AlembicConfig(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

    print("--- [conftest.py] Initiating Test Suite Database Setup (Alembic) ---")
    try:
        print(f"Attempting to connect to and verify test database: {settings.DATABASE_URL}")
        check_engine = create_async_engine(str(settings.DATABASE_URL))
        async with check_engine.connect() as connection:
             await connection.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        await check_engine.dispose()
        print("Test database connectivity verified.")
        
        print("Downgrading test database to 'base'...")
        alembic_command.downgrade(alembic_cfg, "base")
        print("Upgrading test database to 'head'...")
        alembic_command.upgrade(alembic_cfg, "head")
        print("Alembic migrations successfully applied to the test database.")

        print("Verifying 'users' table existence in test database directly after migration...")
        try:
            async with async_app_engine.connect() as conn_check:
                result = await conn_check.execute(text("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'users');"))
                table_exists = result.scalar_one()
            if table_exists:
                print("INFO [conftest.py]: 'users' table confirmed to exist in test database post-migration.")
            else:
                pytest.fail("CRITICAL [conftest.py]: 'users' table DOES NOT EXIST in test database immediately after Alembic upgrade head.")
        except Exception as e_check:
            pytest.fail(f"CRITICAL [conftest.py]: Error while checking for 'users' table existence: {e_check}")

    except Exception as e:
        pytest.fail(f"CRITICAL [conftest.py]: Alembic migration process failed during test setup. Error: {e}\nDB URL used: {settings.DATABASE_URL}")

    if not all([settings.FIRST_SUPERUSER_USERNAME, settings.FIRST_SUPERUSER_EMAIL, settings.FIRST_SUPERUSER_PASSWORD]):
        pytest.fail("CRITICAL [conftest.py]: Admin credentials (FIRST_SUPERUSER_USERNAME, EMAIL, PASSWORD) are not configured in settings.")
    
    print(f"Attempting to create admin user: '{settings.FIRST_SUPERUSER_USERNAME}' in test database.")
    try:
        await create_admin_user(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD
        )
        print(f"Admin user '{settings.FIRST_SUPERUSER_USERNAME}' creation process initiated.")
        
        async with AsyncSessionLocal() as db:
            from app.services.auth_service import get_user_by_username
            user = await get_user_by_username(db, settings.FIRST_SUPERUSER_USERNAME)
            if not user or not user.is_admin:
                pytest.fail(f"CRITICAL [conftest.py]: Admin user '{settings.FIRST_SUPERUSER_USERNAME}' was NOT found or is not an admin in the test DB after creation attempt.")
            print(f"Admin user '{settings.FIRST_SUPERUSER_USERNAME}' successfully verified in test database.")
    except Exception as e:
        pytest.fail(f"CRITICAL [conftest.py]: Failed to create or verify admin user in test database. Error: {e}")
    
    print("--- [conftest.py] Test Suite Database Setup Complete ---")
    
    yield
    
    print("--- [conftest.py] Initiating Test Suite Teardown (Alembic) ---")
    try:
        print(f"Downgrading test database '{settings.DATABASE_URL}' to 'base' to clean up...")
        alembic_command.downgrade(alembic_cfg, "base")
        print("Test database successfully downgraded to 'base'.")
    except Exception as e:
        print(f"WARNING [conftest.py]: Failed to downgrade test database during teardown. Manual cleanup might be needed. Error: {e}")

@pytest.fixture(scope="function")
def client():
    """Provides a TestClient instance for API testing, ensuring app context."""
    if not app:
        pytest.fail("CRITICAL [conftest.py]: FastAPI 'app' is not available. Cannot create TestClient.")
    
    from fastapi.testclient import TestClient # Import here to use the app instance
    # TestClient handles running the async app in a way that sync test functions can call it.
    with TestClient(app) as c: # TestClient itself is sync, but the fixture can be async
        yield c

@pytest.fixture(scope="function")
async def db_session():
    """Provides a clean, async database session for each test function."""
    if not AsyncSessionLocal:
        pytest.fail("CRITICAL [conftest.py]: 'AsyncSessionLocal' is not available. Cannot provide DB session.")
    
    engine_for_this_session_factory = AsyncSessionLocal.kw.get('bind')
    if engine_for_this_session_factory:
        print(f"DEBUG [conftest.py db_session]: AsyncSessionLocal factory is bound to engine with URL: {engine_for_this_session_factory.url}")
    else:
        print("DEBUG [conftest.py db_session]: AsyncSessionLocal factory is NOT bound to an engine (or bind key is not 'bind'). This is unexpected.")
        
    async with AsyncSessionLocal() as session:
        try:
            if session.bind:
                print(f"DEBUG [conftest.py db_session]: Yielding session {id(session)} bound to engine with URL: {session.bind.url}")
                # Explicitly check for 'users' table in *this specific session*
                # 'text' is imported at the end of the file.
                result = await session.execute(text("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'users');"))
                table_exists_in_session = result.scalar_one()
                print(f"DEBUG [conftest.py db_session]: In yielded session, 'users' table exists? {table_exists_in_session}. DB URL: {session.bind.url}")
                if not table_exists_in_session:
                     print(f"CRITICAL DEBUG [conftest.py db_session]: 'users' table NOT FOUND by session provided to test. DB URL: {session.bind.url}")
            else:
                print(f"DEBUG [conftest.py db_session]: Yielding session {id(session)} that is UNBOUND. This is highly unexpected.")
            yield session
        finally:
            await session.close()

# --- Helper Functions (as previously defined) ---
def generate_unique_username(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}_test"

def generate_unique_email(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}@test.plumas.top"

# For the database connectivity check, we need `text` from sqlalchemy
from sqlalchemy import text 