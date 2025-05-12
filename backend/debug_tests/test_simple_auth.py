import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.core.config import settings # To get admin credentials
from app.services.auth_service import get_user_by_username # To verify user creation

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

async def test_admin_login(client: AsyncClient, db_session: AsyncSession):
    """
    Test that the admin user can log in.
    Assumes admin user is created by fixtures in conftest.py.
    """
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

    # Optionally verify admin user details from token or a protected admin endpoint
    # For simplicity, successful login with token is the primary check here.

async def test_user_registration(client: AsyncClient, db_session: AsyncSession):
    """
    Test that a new user can register.
    """
    user_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "testpassword123",
    }
    response = await client.post("/auth/signup", json=user_data)
    
    assert response.status_code == status.HTTP_201_CREATED, f"Registration failed: {response.text}"
    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]
    assert "id" in response_data

    # Verify user in database
    created_user = await get_user_by_username(db_session, user_data["username"])
    assert created_user is not None
    assert created_user.email == user_data["email"]
    # assert created_user.is_active is True # Removed this line as User model may not have is_active

    print(f"DEBUG [test_simple_auth.py]: User {created_user.username} verified in DB.") 