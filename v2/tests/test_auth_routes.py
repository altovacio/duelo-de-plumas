"""
Tests for authentication routes.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import models if needed to check data, though often checking response is enough
from v2 import models 

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio 

async def test_login_success(client: AsyncClient, test_user: models.User):
    """Test successful login with correct credentials."""
    login_data = {
        "username": test_user.username,
        "password": "password" # The password set in the fixture
    }
    response = await client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    response_json = response.json()
    assert "access_token" in response_json
    assert response_json["token_type"] == "bearer"

async def test_login_invalid_password(client: AsyncClient, test_user: models.User):
    """Test login failure with incorrect password."""
    login_data = {
        "username": test_user.username,
        "password": "wrongpassword"
    }
    response = await client.post("/auth/token", data=login_data)
    assert response.status_code == 401 # Unauthorized
    assert "access_token" not in response.json()
    assert response.json()["detail"] == "Incorrect username or password"

async def test_login_invalid_username(client: AsyncClient):
    """Test login failure with non-existent username."""
    login_data = {
        "username": "nonexistentuser",
        "password": "password"
    }
    response = await client.post("/auth/token", data=login_data)
    assert response.status_code == 401 # Unauthorized
    assert "access_token" not in response.json()
    assert response.json()["detail"] == "Incorrect username or password"

async def test_read_users_me_success(client: AsyncClient, test_user: models.User):
    """Test accessing the /auth/users/me endpoint after successful login."""
    # 1. Login to get token
    login_data = {"username": test_user.username, "password": "password"}
    login_response = await client.post("/auth/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Access protected route with correct path
    response = await client.get("/auth/users/me", headers=headers)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["username"] == test_user.username
    assert response_json["email"] == test_user.email
    assert "password_hash" not in response_json # Ensure password hash is not returned

async def test_read_users_me_no_token(client: AsyncClient):
    """Test accessing /auth/users/me without providing a token."""
    response = await client.get("/auth/users/me")
    assert response.status_code == 401 # Unauthorized
    assert response.json()["detail"] == "Not authenticated"

async def test_read_users_me_invalid_token(client: AsyncClient):
    """Test accessing /auth/users/me with an invalid token."""
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await client.get("/auth/users/me", headers=headers)
    assert response.status_code == 401 # Unauthorized
    assert response.json()["detail"] == "Could not validate credentials" # From security.py

# Add tests here later 