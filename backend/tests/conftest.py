# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
import uuid

# Attempt to import app and SessionLocal with error handling for robustness
try:
    from app.main import app
    from app.db.session import SessionLocal
except ImportError as e:
    app = None
    SessionLocal = None
    print(f"Warning: Could not import app or SessionLocal in conftest.py: {e}")
    print("Ensure app.main and app.db.session are correct and accessible from /app in the container.")

@pytest.fixture(scope="session")
def client():
    if not app:
        pytest.fail("FastAPI app could not be imported in conftest.py. Tests cannot run.")
    return TestClient(app)

# Helper function to get a DB session (if needed for setup/cleanup outside of API calls)
# This is not a fixture itself but a utility that can be called by tests if direct DB access is needed.
# Note: FastAPI typically handles DB sessions per request via dependencies.
@pytest.fixture(scope="function") # Or session, depending on how it's used
def db_session():
    if not SessionLocal:
        pytest.skip("SessionLocal could not be imported. Skipping tests requiring direct DB session.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Generate unique usernames and emails for each test run
def generate_unique_username(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}_test"

def generate_unique_email(base="user"):
    return f"{base}_{uuid.uuid4().hex[:8]}@test.plumas.top"

# The following functions are from the original end_to_end_test.py and made available here.
# If test_data is needed as a fixture:
# @pytest.fixture(scope="session")
# def test_data_global():
#     return {} 