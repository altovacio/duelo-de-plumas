"""
Tests for admin routes.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from v2 import models, schemas # Assuming models and schemas are in v2

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# --- AI Writer Admin Tests --- 

async def test_admin_list_ai_writers_empty(base_client: AsyncClient, admin_token: str):
    """Test listing AI writers when none exist."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.get("/admin/ai-writers")
    base_client.headers.pop("Authorization", None)
    assert response.status_code == 200
    assert response.json() == []

async def test_admin_create_ai_writer_success(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test successfully creating a new AI Writer."""
    writer_data = {
        "name": "Test Writer One",
        "description": "A test writer description.",
        "personality_prompt": "Be helpful and creative."
    }
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.post("/admin/ai-writers", json=writer_data)
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["name"] == writer_data["name"]
    assert response_json["description"] == writer_data["description"]
    assert response_json["personality_prompt"] == writer_data["personality_prompt"]
    assert "id" in response_json
    
    # Verify in DB
    writer = await db_session.get(models.AIWriter, response_json["id"])
    assert writer is not None
    assert writer.name == writer_data["name"]

async def test_admin_create_ai_writer_duplicate_name(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test creating an AI Writer fails if the name already exists."""
    # Create initial writer
    initial_writer = models.AIWriter(name="Duplicate Writer", personality_prompt="Prompt 1")
    db_session.add(initial_writer)
    await db_session.commit()
    
    writer_data = {
        "name": "Duplicate Writer", # Same name
        "description": "Second description.",
        "personality_prompt": "Prompt 2"
    }
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.post("/admin/ai-writers", json=writer_data)
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 409 # Conflict
    assert "already exists" in response.json()["detail"]

async def test_admin_list_ai_writers_populated(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test listing AI writers when some exist."""
    w1 = models.AIWriter(name="Writer A", personality_prompt="Prompt A")
    w2 = models.AIWriter(name="Writer B", personality_prompt="Prompt B")
    db_session.add_all([w1, w2])
    await db_session.commit()
    
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.get("/admin/ai-writers")
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 2
    names = {w["name"] for w in response_json}
    assert "Writer A" in names
    assert "Writer B" in names

async def test_admin_get_ai_writer_success(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting a specific AI writer by ID."""
    writer = models.AIWriter(name="GetMe Writer", personality_prompt="Prompt Get")
    db_session.add(writer)
    await db_session.commit()
    await db_session.refresh(writer)
    
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.get(f"/admin/ai-writers/{writer.id}")
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == writer.id
    assert response_json["name"] == writer.name

async def test_admin_get_ai_writer_not_found(base_client: AsyncClient, admin_token: str):
    """Test getting a non-existent AI writer."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.get("/admin/ai-writers/99999")
    base_client.headers.pop("Authorization", None)
    assert response.status_code == 404
    assert response.json()["detail"] == "AI Writer not found"

async def test_admin_update_ai_writer_success(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test successfully updating an AI Writer."""
    writer = models.AIWriter(name="UpdateMe", personality_prompt="Initial Prompt")
    db_session.add(writer)
    await db_session.commit()
    await db_session.refresh(writer)
    
    update_data = {
        "name": "Updated Name",
        "description": "Updated Description"
        # Personality prompt not updated
    }
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.put(f"/admin/ai-writers/{writer.id}", json=update_data)
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["id"] == writer.id
    assert response_json["name"] == update_data["name"]
    assert response_json["description"] == update_data["description"]
    assert response_json["personality_prompt"] == writer.personality_prompt # Unchanged
    
    # Verify in DB
    await db_session.refresh(writer)
    assert writer.name == update_data["name"]
    assert writer.description == update_data["description"]

async def test_admin_update_ai_writer_not_found(base_client: AsyncClient, admin_token: str):
    """Test updating a non-existent AI writer."""
    update_data = {"name": "New Name"}
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.put("/admin/ai-writers/99999", json=update_data)
    base_client.headers.pop("Authorization", None)
    assert response.status_code == 404
    assert response.json()["detail"] == "AI Writer not found"

async def test_admin_delete_ai_writer_success(base_client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test successfully deleting an AI Writer."""
    writer = models.AIWriter(name="DeleteMe", personality_prompt="Delete Prompt")
    db_session.add(writer)
    await db_session.commit()
    await db_session.refresh(writer)
    writer_id = writer.id
    
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.delete(f"/admin/ai-writers/{writer_id}")
    base_client.headers.pop("Authorization", None)
    
    assert response.status_code == 204 # No Content
    
    # Verify deletion in DB
    deleted_writer = await db_session.get(models.AIWriter, writer_id)
    assert deleted_writer is None

async def test_admin_delete_ai_writer_not_found(base_client: AsyncClient, admin_token: str):
    """Test deleting a non-existent AI writer."""
    base_client.headers["Authorization"] = f"Bearer {admin_token}"
    response = await base_client.delete("/admin/ai-writers/99999")
    base_client.headers.pop("Authorization", None)
    assert response.status_code == 404
    assert response.json()["detail"] == "AI Writer not found"

# --- TODO: Add tests for other admin endpoints --- 
# - AI Judge CRUD
# - Contest Judge Assignment
# - Contest Status/Password
# - AI Evaluation Info
# - AI Submission Trigger
# - Submission Deletion

# Add tests here later 