"""
Tests for contest routes.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from backend import models, schemas

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# --- Fixture for a logged-in client --- 

@pytest_asyncio.fixture(scope="function")
async def logged_in_client(client: AsyncClient, test_user: models.User) -> AsyncClient:
    """Provides an AsyncClient instance that is logged in as test_user."""
    login_data = {"username": test_user.username, "password": "password"}
    login_response = await client.post("/auth/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"} # Set headers for subsequent requests
    return client

@pytest_asyncio.fixture(scope="function")
async def admin_logged_in_client(client: AsyncClient, test_user: models.User) -> AsyncClient:
    """Provides an AsyncClient instance that is logged in as test_user."""
    login_data = {"username": test_user.username, "password": "password"}
    login_response = await client.post("/auth/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"} # Set headers for subsequent requests
    return client

# --- Contest Tests --- 

@pytest.mark.asyncio 
async def test_create_public_contest_success(base_client: AsyncClient, admin_token: str):
    """Test creating a new public contest successfully (requires admin)."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    contest_data = {
        "title": "Public Test Contest",
        "description": "A test contest for everyone",
        "contest_type": "public",
        # Start/end dates are optional, let API handle defaults
        "required_judges": 1
    }
    response = await base_client.post("/contests/", json=contest_data)
    assert response.status_code == 201 # Created
    # Clean up header after test if needed, although fixture scope should handle it
    base_client.headers.pop("Authorization", None)
    response_json = response.json()
    assert response_json["title"] == contest_data["title"]
    assert response_json["description"] == contest_data["description"]
    assert response_json["contest_type"] == "public"
    assert response_json["status"] == "open" # Default status
    assert "id" in response_json
    assert "password_hash" not in response_json # Public contest shouldn't have password hash

@pytest.mark.asyncio 
async def test_create_private_contest_success(base_client: AsyncClient, admin_token: str):
    """Test creating a new private contest successfully (requires admin)."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    contest_data = {
        "title": "Private Test Contest",
        "description": "A secret test contest",
        "contest_type": "private",
        "password": "secretpassword", # Required for private
        "required_judges": 2
    }
    response = await base_client.post("/contests/", json=contest_data)
    base_client.headers.pop("Authorization", None) # Cleanup
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["title"] == contest_data["title"]
    assert response_json["contest_type"] == "private"
    assert "id" in response_json
    # Password hash should not be directly exposed, even if set
    assert "password_hash" not in response_json 
    assert "password" not in response_json

@pytest.mark.asyncio 
async def test_create_private_contest_missing_password(base_client: AsyncClient, admin_token: str):
    """Test creating a private contest fails if password is not provided (requires admin)."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    contest_data = {
        "title": "Private No Password",
        "contest_type": "private",
        "required_judges": 1
    }
    response = await base_client.post("/contests/", json=contest_data)
    base_client.headers.pop("Authorization", None) # Cleanup
    # Expecting a validation error or a specific error from the endpoint logic
    assert response.status_code == 422 # Unprocessable Entity (pydantic validation)

async def test_get_contests_list_public(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving a list of public contests."""
    # Create some test contests
    c1 = models.Contest(title="Public Contest 1", contest_type="public")
    c2 = models.Contest(title="Private Contest 1", contest_type="private")
    c3 = models.Contest(title="Public Contest 2", contest_type="public", status="closed")
    db_session.add_all([c1, c2, c3])
    await db_session.commit()

    response = await client.get("/contests/")
    assert response.status_code == 200
    response_json = response.json()
    # Should only return public contests by default
    assert len(response_json) == 2
    titles = {c["title"] for c in response_json}
    assert "Public Contest 1" in titles
    assert "Public Contest 2" in titles
    assert "Private Contest 1" not in titles

# TODO: Add test for getting private contests (requires auth)
# TODO: Add tests for filtering contests (status, type)

async def test_get_contest_detail_public_success(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving details of a specific public contest."""
    contest = models.Contest(title="Detailed Public Contest", description="Desc", contest_type="public")
    db_session.add(contest)
    await db_session.commit()
    await db_session.refresh(contest)

    response = await client.get(f"/contests/{contest.id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == contest.id
    assert response_json["title"] == contest.title
    assert response_json["description"] == contest.description
    assert response_json["contest_type"] == "public"

async def test_get_contest_detail_private_no_auth(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving details of a private contest fails without authentication/password."""
    contest = models.Contest(title="Detailed Private Contest", contest_type="private")
    contest.set_password("privatepass")
    db_session.add(contest)
    await db_session.commit()
    await db_session.refresh(contest)

    response = await client.get(f"/contests/{contest.id}")
    assert response.status_code == 403 # Expect Forbidden now that anonymous reaches the endpoint
    assert "detail" in response.json() # Check for error message

# TODO: Add test for accessing private contest detail WITH correct password/auth

async def test_get_contest_detail_not_found(client: AsyncClient):
    """Test retrieving details of a non-existent contest."""
    response = await client.get("/contests/99999")
    assert response.status_code == 404 # Not Found
    assert response.json()["detail"] == "Contest not found"

# Add tests here later 