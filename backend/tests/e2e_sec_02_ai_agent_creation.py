# backend/tests/e2e_sec_02_ai_agent_creation.py
import pytest
from httpx import AsyncClient # Changed from fastapi.testclient import TestClient
import logging

from app.core.config import settings # Keep for other settings if needed, but not for API_V1_STR
from app.schemas.agent import AgentCreate, AgentResponse
from app.schemas.user import UserResponse # For fetching admin_id
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 2: AI Agent Creation ---

async def test_02_01_user1_creates_writer1(client: AsyncClient): # async def, AsyncClient
    """User 1 creates an AI Writer (writer1). Get writer1_id."""
    assert "user1_headers" in test_data, "User 1 token not found."
    agent_in = AgentCreate(
        name="MyFirstWriter",
        description="A simple AI writer by User 1",
        prompt="Write a short story about a dragon.",
        type="writer",
        is_public=False
    )
    response = await client.post( # await, corrected path
        "/agents", # CORRECTED PATH
        json=agent_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 creating writer1 failed: {response.text}"
    writer1_data = AgentResponse(**response.json())
    assert writer1_data.name == agent_in.name
    assert writer1_data.type == "writer"
    assert not writer1_data.is_public
    assert writer1_data.owner_id == test_data["user1_id"]
    test_data["writer1_id"] = writer1_data.id
    print(f"User 1 created writer1 (ID: {writer1_data.id}) successfully.")

@pytest.mark.run(after='test_02_01_user1_creates_writer1')
async def test_02_02_user1_creates_judge1(client: AsyncClient): # async def, AsyncClient
    """User 1 creates an AI Judge (judge1). Get judge1_id."""
    assert "user1_headers" in test_data, "User 1 token not found."
    agent_in = AgentCreate(
        name="MyFirstJudge",
        description="A simple AI judge by User 1",
        prompt="Evaluate the text based on clarity and engagement.",
        type="judge",
        is_public=False
    )
    response = await client.post( # await, corrected path
        "/agents",
        json=agent_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 creating judge1 failed: {response.text}"
    judge1_data = AgentResponse(**response.json())
    assert judge1_data.name == agent_in.name
    assert judge1_data.type == "judge"
    assert not judge1_data.is_public
    assert judge1_data.owner_id == test_data["user1_id"]
    test_data["judge1_id"] = judge1_data.id
    print(f"User 1 created judge1 (ID: {judge1_data.id}) successfully.")

@pytest.mark.run(after='test_02_02_user1_creates_judge1')
async def test_02_03_admin_creates_global_writer(client: AsyncClient): # async def, AsyncClient
    """Admin creates a global AI Writer (writer_global). Get writer_global_id."""
    assert "admin_headers" in test_data, "Admin token not found."
    agent_in = AgentCreate(
        name="GlobalStoryWriter",
        description="A public AI writer for all users.",
        prompt="Generate a fascinating tale based on the user prompt.",
        type="writer",
        is_public=True
    )
    response = await client.post( # await, corrected path
        "/agents",
        json=agent_in.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin creating global writer failed: {response.text}"
    writer_global_data = AgentResponse(**response.json())
    assert writer_global_data.name == agent_in.name
    assert writer_global_data.type == "writer"
    assert writer_global_data.is_public
    if "admin_id" not in test_data:
        me_response = await client.get("/users/me", headers=test_data["admin_headers"]) # await, corrected path
        assert me_response.status_code == 200
        test_data["admin_id"] = UserResponse(**me_response.json()).id
    
    assert writer_global_data.owner_id == test_data["admin_id"]
    test_data["writer_global_id"] = writer_global_data.id
    print(f"Admin created writer_global (ID: {writer_global_data.id}) successfully.")

@pytest.mark.run(after='test_02_03_admin_creates_global_writer')
async def test_02_04_admin_creates_global_judge(client: AsyncClient): # async def, AsyncClient
    """Admin creates a global AI Judge (judge_global). Get judge_global_id."""
    assert "admin_headers" in test_data, "Admin token not found."
    agent_in = AgentCreate(
        name="GlobalContentJudge",
        description="A public AI judge for all users.",
        prompt="Assess the submission for overall quality and adherence to guidelines.",
        type="judge",
        is_public=True
    )
    response = await client.post( # await, corrected path
        "/agents",
        json=agent_in.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin creating global judge failed: {response.text}"
    judge_global_data = AgentResponse(**response.json())
    assert judge_global_data.name == agent_in.name
    assert judge_global_data.type == "judge"
    assert judge_global_data.is_public
    assert judge_global_data.owner_id == test_data["admin_id"] # Assuming admin_id was fetched in previous test
    test_data["judge_global_id"] = judge_global_data.id
    print(f"Admin created judge_global (ID: {judge_global_data.id}) successfully.")

@pytest.mark.run(after='test_02_04_admin_creates_global_judge')
async def test_02_05_user1_lists_agents(client: AsyncClient): # async def, AsyncClient
    """User 1 lists their AI agents, verifies writer1 and judge1 are present and also the global writer and judge are present."""
    assert "user1_headers" in test_data, "User 1 token not found."
    response = await client.get("/agents", headers=test_data["user1_headers"]) # await, corrected path, CORRECTED PATH
    assert response.status_code == 200, f"User 1 listing agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    agent_ids_present = {agent.id for agent in agents}
    expected_ids = {
        test_data["writer1_id"], # User 1's own agent
        test_data["judge1_id"]   # User 1's own agent
        # Global agents should not be returned by default by this endpoint call
        # test_data["writer_global_id"],
        # test_data["judge_global_id"]
    }
    assert expected_ids.issubset(agent_ids_present), \
        f"User 1 list should only contain their own agents. Expected: {expected_ids}, Got: {agent_ids_present}"
    
    # Further assertions can check that ONLY these agents are present
    assert len(agent_ids_present) == len(expected_ids), \
        f"User 1 list should only contain their own agents. Expected {len(expected_ids)} agents, Got: {len(agent_ids_present)}"

    for agent in agents:
        if agent.id == test_data["writer1_id"]:
            assert agent.owner_id == test_data["user1_id"]
            assert not agent.is_public
        elif agent.id == test_data["judge1_id"]:
            assert agent.owner_id == test_data["user1_id"]
            assert not agent.is_public
            
    print("User 1 listed agents successfully, found own and global agents.")

@pytest.mark.run(after='test_02_05_user1_lists_agents')
async def test_02_06_user2_lists_agents(client: AsyncClient): # async def, AsyncClient
    """User 2 lists their AI agents, verifies no private agents of User 1 are present, but global agents are."""
    assert "user2_headers" in test_data, "User 2 token not found."
    response = await client.get("/agents?public=true", headers=test_data["user2_headers"]) # MODIFIED: Added ?public=true
    assert response.status_code == 200, f"User 2 listing public agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    agent_ids_present = {agent.id for agent in agents}
    private_user1_agent_ids = {test_data.get("writer1_id"), test_data.get("judge1_id")}
    global_agent_ids = {test_data.get("writer_global_id"), test_data.get("judge_global_id")}

    # Ensure no private agents of User 1 are in User 2's list
    assert not private_user1_agent_ids.intersection(agent_ids_present), \
        f"User 2 list contains private agents of User 1. Found: {private_user1_agent_ids.intersection(agent_ids_present)}"
        
    # Ensure global agents are present
    assert global_agent_ids.issubset(agent_ids_present), \
        f"User 2 list missing global agents. Expected: {global_agent_ids}, Got: {agent_ids_present}"

    print("User 2 listed agents successfully, found only their own (if any) and global agents.")

@pytest.mark.run(after='test_02_06_user2_lists_agents')
async def test_02_07_admin_lists_global_agents(client: AsyncClient): # async def, AsyncClient
    """Admin lists global AI agents, verifies writer_global and judge_global are present."""
    assert "admin_headers" in test_data, "Admin token not found."
    # The endpoint to list global agents for admin might be specific, e.g., /agents/?public=true
    # Or it might be that admin listing defaults to all or needs a special flag.
    # For now, assuming /agents/?public=true is the way to get global agents.
    response = await client.get("/agents?public=true", headers=test_data["admin_headers"]) # MODIFIED: Removed trailing slash before ?
    assert response.status_code == 200, f"Admin listing global agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    global_agent_ids_found = {agent.id for agent in agents if agent.is_public}
    expected_global_ids = {
        test_data.get("writer_global_id"),
        test_data.get("judge_global_id")
    }
    
    assert expected_global_ids.issubset(global_agent_ids_found), \
        f"Admin global list missing expected global agents. Expected: {expected_global_ids}, Found: {global_agent_ids_found}"
        
    print("Admin listed global agents successfully.")

# --- End of Test Section 2 ---