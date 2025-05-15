# backend/tests/e2e_sec_01_setup_user_registration.py
import pytest
from httpx import AsyncClient # Changed from fastapi.testclient import TestClient
import logging

from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserCredit, Token
from tests.shared_test_state import test_data
from tests.conftest import generate_unique_username, generate_unique_email # Import helpers

# client will be a fixture argument, e.g. async def test_01_01_admin_login(client: AsyncClient):

# --- Start of Test Section 1: Setup & User Registration ---

async def test_01_01_admin_login(client: AsyncClient): # Changed to async def, client: AsyncClient
    """Admin logs in (obtain admin_token)."""
    response = await client.post( # Added await
        "/auth/login",
        data={"username": settings.FIRST_SUPERUSER_USERNAME, "password": settings.FIRST_SUPERUSER_PASSWORD},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token_data = Token(**response.json())
    assert token_data.access_token
    assert token_data.token_type == "bearer"
    test_data["admin_token"] = token_data.access_token
    test_data["admin_headers"] = {"Authorization": f"Bearer {token_data.access_token}"}
    # Retrieve admin user details to get admin_user_id
    admin_me_resp = await client.get(
        "/users/me",
        headers=test_data["admin_headers"]
    )
    assert admin_me_resp.status_code == 200, f"Failed to fetch admin user details: {admin_me_resp.text}"
    admin_me_data = UserResponse(**admin_me_resp.json())
    test_data["admin_user_id"] = admin_me_data.id
    print("Admin login successful.")

@pytest.mark.run(after='test_01_01_admin_login')
async def test_01_02_user1_registers_self(client: AsyncClient): # Changed to async def, client: AsyncClient
    """User 1 registers themselves."""
    test_data["user1_username"] = generate_unique_username("user1")
    test_data["user1_email"] = generate_unique_email("user1")
    test_data["user1_password"] = "testpassword1"

    user_in = UserCreate(
        username=test_data["user1_username"],
        email=test_data["user1_email"],
        password=test_data["user1_password"]
    )
    response = await client.post("/auth/signup", json=user_in.model_dump()) # Added await
    assert response.status_code == 201, f"User 1 registration failed: {response.text}"
    user1_data = UserResponse(**response.json())
    assert user1_data.username == test_data["user1_username"]
    assert user1_data.email == test_data["user1_email"]
    assert user1_data.credits == 0, "User 1 initial credits should be 0"
    assert not user1_data.is_admin
    test_data["user1_id"] = user1_data.id
    print(f"User 1 ({test_data['user1_username']}) registered successfully.")

@pytest.mark.run(after='test_01_02_user1_registers_self')
async def test_01_03_user1_login(client: AsyncClient): # Changed to async def, client: AsyncClient
    """Obtain user1_token after login."""
    login_data = UserLogin(username=test_data["user1_username"], password=test_data["user1_password"])
    response = await client.post( # Added await
        "/auth/login", data=login_data.model_dump()
    )
    assert response.status_code == 200, f"User 1 login failed: {response.text}"
    token_data = Token(**response.json())
    assert token_data.access_token
    test_data["user1_token"] = token_data.access_token
    test_data["user1_headers"] = {"Authorization": f"Bearer {token_data.access_token}"}
    print(f"User 1 ({test_data['user1_username']}) login successful.")

@pytest.mark.run(after='test_01_03_user1_login')
async def test_01_04_admin_registers_user2(client: AsyncClient): # Changed to async def, client: AsyncClient
    """Admin registers User 2."""
    assert "admin_headers" in test_data, "Admin token not found, ensure admin login test passed."
    test_data["user2_username"] = generate_unique_username("user2")
    test_data["user2_email"] = generate_unique_email("user2")
    test_data["user2_password"] = "testpassword2"

    user_in = UserCreate(
        username=test_data["user2_username"],
        email=test_data["user2_email"],
        password=test_data["user2_password"]
    )
    response = await client.post( # Added await
        "/auth/signup", 
        json=user_in.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 201, f"Admin registering User 2 failed: {response.text}"
    user2_data = UserResponse(**response.json())
    assert user2_data.username == test_data["user2_username"]
    assert user2_data.email == test_data["user2_email"]
    assert user2_data.credits == 0, "User 2 initial credits should be 0"
    assert not user2_data.is_admin 
    test_data["user2_id"] = user2_data.id
    print(f"Admin registered User 2 ({test_data['user2_username']}) successfully.")

@pytest.mark.run(after='test_01_04_admin_registers_user2')
async def test_01_05_user2_login(client: AsyncClient): # Changed to async def, client: AsyncClient
    """User 2 logs in (obtain user2_token)."""
    login_data = UserLogin(username=test_data["user2_username"], password=test_data["user2_password"])
    response = await client.post( # Added await
        "/auth/login", data=login_data.model_dump()
    )
    assert response.status_code == 200, f"User 2 login failed: {response.text}"
    token_data = Token(**response.json())
    assert token_data.access_token
    test_data["user2_token"] = token_data.access_token
    test_data["user2_headers"] = {"Authorization": f"Bearer {token_data.access_token}"}
    print(f"User 2 ({test_data['user2_username']}) login successful.")

@pytest.mark.run(after='test_01_05_user2_login')
async def test_01_06_admin_verifies_users(client: AsyncClient): # Changed to async def, client: AsyncClient
    """Admin verifies User 1 and User 2 details and credit balances."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data and "user2_id" in test_data, "User IDs not found."

    response_user1 = await client.get( # Added await
        f"/users/{test_data['user1_id']}",
        headers=test_data["admin_headers"]
    )
    assert response_user1.status_code == 200, f"Admin fetching User 1 failed: {response_user1.text}"
    user1_data = UserResponse(**response_user1.json())
    assert user1_data.id == test_data["user1_id"]
    assert user1_data.credits == 0
    print(f"Admin verified User 1 ({user1_data.username}) details successfully.")

    response_user2 = await client.get( # Added await
        f"/users/{test_data['user2_id']}",
        headers=test_data["admin_headers"]
    )
    assert response_user2.status_code == 200, f"Admin fetching User 2 failed: {response_user2.text}"
    user2_data = UserResponse(**response_user2.json())
    assert user2_data.id == test_data["user2_id"]
    assert user2_data.credits == 0
    print(f"Admin verified User 2 ({user2_data.username}) details successfully.")

# --- End of Test Section 1 ---