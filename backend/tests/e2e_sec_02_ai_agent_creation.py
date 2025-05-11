# backend/tests/e2e_sec_02_ai_agent_creation.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
import logging

from app.core.config import settings
from app.schemas.agent import AgentCreate, AgentResponse
from app.schemas.user import UserResponse # For fetching admin_id
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 2: AI Agent Creation ---

def test_02_01_user1_creates_writer1(client: TestClient):
    """User 1 creates an AI Writer (writer1). Get writer1_id."""
    assert "user1_headers" in test_data, "User 1 token not found."
    agent_in = AgentCreate(
        name="MyFirstWriter",
        description="A simple AI writer by User 1",
        prompt="Write a short story about a dragon.",
        type="writer",
        is_public=False
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/",
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
def test_02_02_user1_creates_judge1(client: TestClient):
    """User 1 creates an AI Judge (judge1). Get judge1_id."""
    assert "user1_headers" in test_data, "User 1 token not found."
    agent_in = AgentCreate(
        name="MyFirstJudge",
        description="A simple AI judge by User 1",
        prompt="Evaluate the text based on clarity and engagement.",
        type="judge",
        is_public=False
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/",
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
def test_02_03_admin_creates_global_writer(client: TestClient):
    """Admin creates a global AI Writer (writer_global). Get writer_global_id."""
    assert "admin_headers" in test_data, "Admin token not found."
    agent_in = AgentCreate(
        name="GlobalStoryWriter",
        description="A public AI writer for all users.",
        prompt="Generate a fascinating tale based on the user prompt.",
        type="writer",
        is_public=True
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/",
        json=agent_in.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin creating global writer failed: {response.text}"
    writer_global_data = AgentResponse(**response.json())
    assert writer_global_data.name == agent_in.name
    assert writer_global_data.type == "writer"
    assert writer_global_data.is_public
    if "admin_id" not in test_data:
        me_response = client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["admin_headers"])
        assert me_response.status_code == 200
        test_data["admin_id"] = UserResponse(**me_response.json()).id
    
    assert writer_global_data.owner_id == test_data["admin_id"]
    test_data["writer_global_id"] = writer_global_data.id
    print(f"Admin created writer_global (ID: {writer_global_data.id}) successfully.")

@pytest.mark.run(after='test_02_03_admin_creates_global_writer')
def test_02_04_admin_creates_global_judge(client: TestClient):
    """Admin creates a global AI Judge (judge_global). Get judge_global_id."""
    assert "admin_headers" in test_data, "Admin token not found."
    agent_in = AgentCreate(
        name="GlobalFairJudge",
        description="A public AI judge for evaluating texts.",
        prompt="Assess the submission for originality, coherence, and impact.",
        type="judge",
        is_public=True
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/",
        json=agent_in.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin creating global judge failed: {response.text}"
    judge_global_data = AgentResponse(**response.json())
    assert judge_global_data.name == agent_in.name
    assert judge_global_data.type == "judge"
    assert judge_global_data.is_public
    assert judge_global_data.owner_id == test_data["admin_id"] 
    test_data["judge_global_id"] = judge_global_data.id
    print(f"Admin created judge_global (ID: {judge_global_data.id}) successfully.")

@pytest.mark.run(after='test_02_04_admin_creates_global_judge')
def test_02_05_user1_lists_agents(client: TestClient):
    """User 1 lists their AI agents, verifies writer1 and judge1 are present and also the global writer and judge are present."""
    assert "user1_headers" in test_data, "User 1 token not found."
    response = client.get(f"{settings.API_V1_STR}/agents/", headers=test_data["user1_headers"])
    assert response.status_code == 200, f"User 1 listing agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    agent_ids_present = {agent.id for agent in agents}
    expected_ids = {
        test_data["writer1_id"],
        test_data["judge1_id"],
        test_data["writer_global_id"],
        test_data["judge_global_id"]
    }
    assert expected_ids.issubset(agent_ids_present), \
        f"User 1 list missing expected agents. Expected: {expected_ids}, Got: {agent_ids_present}"
    
    for agent in agents:
        if agent.id == test_data["writer1_id"]:
            assert agent.owner_id == test_data["user1_id"]
            assert not agent.is_public
        elif agent.id == test_data["judge1_id"]:
            assert agent.owner_id == test_data["user1_id"]
            assert not agent.is_public
        elif agent.id == test_data["writer_global_id"]:
            assert agent.is_public
        elif agent.id == test_data["judge_global_id"]:
            assert agent.is_public
            
    print("User 1 listed agents successfully, found own and global agents.")

@pytest.mark.run(after='test_02_05_user1_lists_agents')
def test_02_06_user2_lists_agents(client: TestClient):
    """User 2 lists their AI agents, verifies they see none but the global writer and judge."""
    assert "user2_headers" in test_data, "User 2 token not found."
    response = client.get(f"{settings.API_V1_STR}/agents/", headers=test_data["user2_headers"])
    assert response.status_code == 200, f"User 2 listing agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    agent_ids_present = {agent.id for agent in agents}
    global_agent_ids = {test_data["writer_global_id"], test_data["judge_global_id"]}
    
    assert global_agent_ids.issubset(agent_ids_present), \
        f"User 2 list missing global agents. Expected subset: {global_agent_ids}, Got: {agent_ids_present}"
    
    private_user1_agents = {test_data["writer1_id"], test_data["judge1_id"]}
    assert not private_user1_agents.intersection(agent_ids_present), \
        f"User 2 list contains private agents of User 1. Disallowed: {private_user1_agents.intersection(agent_ids_present)}"

    for agent in agents:
        assert agent.is_public, f"User 2 sees non-public agent: {agent.name} (ID: {agent.id}) which is not theirs."
        assert agent.id in global_agent_ids
            
    print("User 2 listed agents successfully, found only global agents.")

@pytest.mark.run(after='test_02_06_user2_lists_agents')
def test_02_07_admin_lists_all_agents(client: TestClient):
    """Admin lists global AI agents, verifies they see all four agents."""
    assert "admin_headers" in test_data, "Admin token not found."
    response = client.get(f"{settings.API_V1_STR}/agents/", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin listing agents failed: {response.text}"
    agents = [AgentResponse(**agent) for agent in response.json()]
    
    agent_ids_present = {agent.id for agent in agents}
    all_created_agent_ids = {
        test_data["writer1_id"],
        test_data["judge1_id"],
        test_data["writer_global_id"],
        test_data["judge_global_id"]
    }
    assert all_created_agent_ids.issubset(agent_ids_present), \
        f"Admin list missing expected agents. Expected: {all_created_agent_ids}, Got: {agent_ids_present}"
    print("Admin listed agents successfully, found all created agents.")

# --- End of Test Section 2 ---