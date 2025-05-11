# backend/tests/e2e_sec_04_text_creation.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
import logging

from app.core.config import settings
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.schemas.user import UserResponse, UserCredit # For credit checks and assignments
from app.schemas.agent import AgentExecute # For agent execution
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 4: Text Creation ---

def test_04_01_user1_creates_text1_1_manually(client: TestClient):
    """User 1 creates a text (Text 1.1) using the manual text editor."""
    assert "user1_headers" in test_data, "User 1 token not found."
    text_in = TextCreate(
        title="User1's First Masterpiece",
        content="# Chapter 1\nIt was a dark and stormy night...",
        author="User1 Author Name"
    )
    response = client.post(
        f"{settings.API_V1_STR}/texts/",
        json=text_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 creating text1.1 failed: {response.text}"
    text1_1_data = TextResponse(**response.json())
    assert text1_1_data.title == text_in.title
    assert text1_1_data.content == text_in.content
    assert text1_1_data.author == text_in.author
    assert text1_1_data.owner_id == test_data["user1_id"]
    test_data["text1_1_id"] = text1_1_data.id
    print(f"User 1 created text1.1 (ID: {test_data['text1_1_id']}) manually successfully.")

@pytest.mark.run(after='test_04_01_user1_creates_text1_1_manually')
def test_04_02_user2_creates_text2_1_manually(client: TestClient):
    """User 2 creates a text (Text 2.1) using the manual text editor."""
    assert "user2_headers" in test_data, "User 2 token not found."
    text_in = TextCreate(
        title="User2's Gripping Tale",
        content="## Prologue\nOnce upon a time, in a land far, far away...",
        author="User2 Pen Name"
    )
    response = client.post(
        f"{settings.API_V1_STR}/texts/",
        json=text_in.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 creating text2.1 failed: {response.text}"
    text2_1_data = TextResponse(**response.json())
    assert text2_1_data.title == text_in.title
    assert text2_1_data.content == text_in.content
    assert text2_1_data.author == text_in.author
    assert text2_1_data.owner_id == test_data["user2_id"]
    test_data["text2_1_id"] = text2_1_data.id
    print(f"User 2 created text2.1 (ID: {test_data['text2_1_id']}) manually successfully.")

@pytest.mark.run(after='test_04_02_user2_creates_text2_1_manually')
def test_04_03_user1_views_text2_1_succeeds(client: TestClient):
    """User 1 attempts to view Text 2.1 details -> Succeeds (texts are public by default)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    response = client.get(
        f"{settings.API_V1_STR}/texts/{test_data['text2_1_id']}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 viewing text2.1 failed: {response.text}"
    text_data = TextResponse(**response.json())
    assert text_data.id == test_data["text2_1_id"]
    print("User 1 successfully viewed Text 2.1 details.")

@pytest.mark.run(after='test_04_03_user1_views_text2_1_succeeds')
def test_04_04_user1_edits_text2_1_fails(client: TestClient):
    """User 1 tries to edit Text 2.1 -> Fails (only owners can edit their texts)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    update_payload = TextUpdate(content="User 1 trying to maliciously edit this.")
    response = client.put(
        f"{settings.API_V1_STR}/texts/{test_data['text2_1_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 editing text2.1 should fail (403), but got {response.status_code}: {response.text}"
    print("User 1 attempt to edit Text 2.1 failed as expected (403 Forbidden).")

@pytest.mark.run(after='test_04_04_user1_edits_text2_1_fails')
def test_04_05_user2_edits_text2_1_succeeds(client: TestClient):
    """User 2 edits Text 2.1 -> Succeeds."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    new_content = "## Prologue\nOnce upon a time, in a land far, far away... User 2 made an edit!"
    update_payload = TextUpdate(content=new_content)
    response = client.put(
        f"{settings.API_V1_STR}/texts/{test_data['text2_1_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 editing text2.1 failed: {response.text}"
    updated_text = TextResponse(**response.json())
    assert updated_text.content == new_content
    print("User 2 successfully edited Text 2.1.")

@pytest.mark.run(after='test_04_05_user2_edits_text2_1_succeeds')
def test_04_06_user1_uses_writer1_no_credits_fails(client: TestClient):
    """User 1 tries to use writer1 to generate a text -> Fails (no credits)."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    user_response = client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"])
    assert user_response.status_code == 200
    initial_credits = UserResponse(**user_response.json()).credits
    assert initial_credits == 0, "User 1 initial credits are not 0 before testing no-credit failure."

    execute_payload = AgentExecute(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest", 
        title="Text Gen Attempt No Credits"
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 402, f"User 1 using writer1 with no credits should fail (402 Payment Required), got {response.status_code}: {response.text}"
    
    user_response_after = client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"])
    assert user_response_after.status_code == 200
    assert UserResponse(**user_response_after.json()).credits == initial_credits
    print("User 1 using writer1 with no credits failed as expected (402), credits unchanged.")

@pytest.mark.run(after='test_04_06_user1_uses_writer1_no_credits_fails')
def test_04_07_admin_assigns_credits(client: TestClient):
    """Admin assigns 50 credits to User 1 and 100 credits to User 2."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data and "user2_id" in test_data, "User IDs not found."

    credits_user1 = UserCredit(credits=50)
    response_u1 = client.post(
        f"{settings.API_V1_STR}/admin/users/{test_data['user1_id']}/credits", 
        json=credits_user1.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u1.status_code == 200, f"Admin assigning credits to User 1 failed: {response_u1.text}"
    assert UserResponse(**response_u1.json()).credits == 50
    print(f"Admin assigned 50 credits to User 1 (ID: {test_data['user1_id']}).")

    credits_user2 = UserCredit(credits=100)
    response_u2 = client.post(
        f"{settings.API_V1_STR}/admin/users/{test_data['user2_id']}/credits", 
        json=credits_user2.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u2.status_code == 200, f"Admin assigning credits to User 2 failed: {response_u2.text}"
    assert UserResponse(**response_u2.json()).credits == 100
    print(f"Admin assigned 100 credits to User 2 (ID: {test_data['user2_id']}).")

@pytest.mark.run(after='test_04_07_admin_assigns_credits')
def test_04_08_user1_uses_writer1_with_credits_succeeds(client: TestClient):
    """User 1 attempts to use writer1 to generate a text -> Succeeds, creating Text 1.2."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    user_response_before = client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"])
    initial_credits_user1 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user1 > 0, "User 1 has no credits before attempting AI generation."

    execute_payload = AgentExecute(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest",
        title="AI Generated Story by User1",
        description="A short story generated by writer1."
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 using writer1 with credits failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data, "Agent execution response missing result_id (new text ID)."
    assert "credits_used" in exec_response_data, "Agent execution response missing credits_used."
    
    test_data["text1_2_id"] = exec_response_data["result_id"]
    credits_used_user1 = exec_response_data["credits_used"]
    assert credits_used_user1 > 0, "Credits used should be greater than 0."
    test_data["text1_2_cost"] = credits_used_user1

    text_response = client.get(f"{settings.API_V1_STR}/texts/{test_data['text1_2_id']}", headers=test_data["user1_headers"])
    assert text_response.status_code == 200
    new_text = TextResponse(**text_response.json())
    assert new_text.title == execute_payload.title
    assert new_text.owner_id == test_data["user1_id"]
    print(f"User 1 created AI-generated Text 1.2 (ID: {test_data['text1_2_id']}) successfully.")

    user_response_after = client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"])
    final_credits_user1 = UserResponse(**user_response_after.json()).credits
    assert final_credits_user1 == initial_credits_user1 - credits_used_user1, "User 1 credit balance did not decrease correctly."
    print(f"User 1 credits decreased from {initial_credits_user1} to {final_credits_user1} (cost: {credits_used_user1}).")

    user_response_user2 = client.get(f"{settings.API_V1_STR}/users/{test_data['user2_id']}", headers=test_data["admin_headers"]) 
    initial_credits_user2 = UserResponse(**user_response_user2.json()).credits 
    print(f"User 2 credits remain: {initial_credits_user2}. This test does not modify them.")

@pytest.mark.run(after='test_04_08_user1_uses_writer1_with_credits_succeeds')
def test_04_09_user2_uses_writer1_fails(client: TestClient):
    """User 2 attempts to use writer1 (User 1's private agent) -> Fails."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    execute_payload = AgentExecute(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest",
        title="Attempt by User2 on User1 Agent"
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [403, 404], \
        f"User 2 using User1's writer1 should fail (403/404), got {response.status_code}: {response.text}"
    print("User 2 attempt to use User1's private writer1 failed as expected.")

@pytest.mark.run(after='test_04_09_user2_uses_writer1_fails')
def test_04_10_user2_uses_global_writer_succeeds(client: TestClient):
    """User 2 uses the global writer (writer_global) to generate a text (Text 2.2)."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "writer_global_id" in test_data, "Global Writer ID not found."

    user_response_before = client.get(f"{settings.API_V1_STR}/users/{test_data['user2_id']}", headers=test_data["user2_headers"])
    initial_credits_user2 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user2 > 0, "User 2 has no credits before attempting AI generation."

    execute_payload = AgentExecute(
        agent_id=test_data["writer_global_id"],
        model="claude-3-5-haiku-latest",
        title="AI Generated Story by User2 via Global Writer",
        description="A short story generated by writer_global for User2."
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 using writer_global failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data
    assert "credits_used" in exec_response_data
    
    test_data["text2_2_id"] = exec_response_data["result_id"]
    credits_used_user2 = exec_response_data["credits_used"]
    assert credits_used_user2 > 0
    test_data["text2_2_cost"] = credits_used_user2

    text_response = client.get(f"{settings.API_V1_STR}/texts/{test_data['text2_2_id']}", headers=test_data["user2_headers"])
    assert text_response.status_code == 200
    new_text = TextResponse(**text_response.json())
    assert new_text.title == execute_payload.title
    assert new_text.owner_id == test_data["user2_id"]
    print(f"User 2 created AI-generated Text 2.2 (ID: {test_data['text2_2_id']}) using global writer successfully.")

    user_response_after = client.get(f"{settings.API_V1_STR}/users/{test_data['user2_id']}", headers=test_data["user2_headers"])
    final_credits_user2 = UserResponse(**user_response_after.json()).credits
    assert final_credits_user2 == initial_credits_user2 - credits_used_user2, "User 2 credit balance did not decrease correctly."
    print(f"User 2 credits decreased from {initial_credits_user2} to {final_credits_user2} (cost: {credits_used_user2}).")

    user_response_user1 = client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["admin_headers"])
    user1_credits_current = UserResponse(**user_response_user1.json()).credits
    print(f"User 1 credits remain: {user1_credits_current} (unaffected by User 2 action).")

@pytest.mark.run(after='test_04_10_user2_uses_global_writer_succeeds')
def test_04_11_user1_creates_text1_3_manually(client: TestClient):
    """User 1 creates another text (Text 1.3) manually."""
    assert "user1_headers" in test_data
    text_in = TextCreate(title="User1's Second Manual Text", content="More content from User1.", author="User1 Author Name")
    response = client.post(f"{settings.API_V1_STR}/texts/", json=text_in.model_dump(), headers=test_data["user1_headers"])
    assert response.status_code == 200
    test_data["text1_3_id"] = TextResponse(**response.json()).id
    print(f"User 1 created manual Text 1.3 (ID: {test_data['text1_3_id']}).")

@pytest.mark.run(after='test_04_11_user1_creates_text1_3_manually')
def test_04_12_user2_creates_text2_3_manually(client: TestClient):
    """User 2 creates another text (Text 2.3) manually."""
    assert "user2_headers" in test_data
    text_in = TextCreate(title="User2's Second Manual Text", content="More content from User2.", author="User2 Pen Name")
    response = client.post(f"{settings.API_V1_STR}/texts/", json=text_in.model_dump(), headers=test_data["user2_headers"])
    assert response.status_code == 200
    test_data["text2_3_id"] = TextResponse(**response.json()).id
    print(f"User 2 created manual Text 2.3 (ID: {test_data['text2_3_id']}).")

@pytest.mark.run(after='test_04_12_user2_creates_text2_3_manually')
def test_04_13_admin_creates_text3_1_manually(client: TestClient):
    """Admin creates a text (Text 3.1) manually."""
    assert "admin_headers" in test_data and "admin_id" in test_data
    text_in = TextCreate(title="Admin's Manual Text", content="Admin was here.", author="The Admin")
    response = client.post(f"{settings.API_V1_STR}/texts/", json=text_in.model_dump(), headers=test_data["admin_headers"])
    assert response.status_code == 200
    text_data_resp = TextResponse(**response.json())
    test_data["text3_1_id"] = text_data_resp.id
    assert text_data_resp.owner_id == test_data["admin_id"]
    print(f"Admin created manual Text 3.1 (ID: {test_data['text3_1_id']}).")

@pytest.mark.run(after='test_04_13_admin_creates_text3_1_manually')
def test_04_14_admin_uses_writer_global_succeeds(client: TestClient):
    """Admin uses writer_global to create a text (Text 3.2). Verify transaction recorded against admin."""
    assert "admin_headers" in test_data and "admin_id" in test_data
    assert "writer_global_id" in test_data

    execute_payload = AgentExecute(
        agent_id=test_data["writer_global_id"],
        model="claude-3-5-haiku-latest",
        title="Admin AI Text via Global Writer",
        description="Admin using global AI capabilities."
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin using writer_global failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data and "credits_used" in exec_response_data
    test_data["text3_2_id"] = exec_response_data["result_id"]
    test_data["text3_2_cost"] = exec_response_data["credits_used"]
    assert test_data["text3_2_cost"] > 0

    text_response = client.get(f"{settings.API_V1_STR}/texts/{test_data['text3_2_id']}", headers=test_data["admin_headers"])
    assert text_response.status_code == 200
    assert TextResponse(**text_response.json()).owner_id == test_data["admin_id"]
    print(f"Admin created AI-generated Text 3.2 (ID: {test_data['text3_2_id']}) using writer_global. Cost: {test_data['text3_2_cost']}.")

@pytest.mark.run(after='test_04_14_admin_uses_writer_global_succeeds')
def test_04_15_admin_uses_user1_writer1_succeeds(client: TestClient):
    """Admin uses writer1 (User1's private agent) to create a text (Text 3.3). Verify transaction recorded against admin."""
    assert "admin_headers" in test_data and "admin_id" in test_data
    assert "writer1_id" in test_data 
    assert "user1_id" in test_data

    user1_credits_before_admin_use = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["admin_headers"]).json()).credits

    execute_payload = AgentExecute(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest",
        title="Admin AI Text via User1's Writer1",
        description="Admin using User1's private AI agent."
    )
    response = client.post(
        f"{settings.API_V1_STR}/agents/execute",
        json=execute_payload.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin using User1's writer1 failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data and "credits_used" in exec_response_data
    test_data["text3_3_id"] = exec_response_data["result_id"]
    test_data["text3_3_cost"] = exec_response_data["credits_used"]
    assert test_data["text3_3_cost"] > 0

    text_response = client.get(f"{settings.API_V1_STR}/texts/{test_data['text3_3_id']}", headers=test_data["admin_headers"])
    assert text_response.status_code == 200
    new_text = TextResponse(**text_response.json())
    assert new_text.owner_id == test_data["admin_id"] 
    print(f"Admin created AI-generated Text 3.3 (ID: {test_data['text3_3_id']}) using User1's writer1. Cost: {test_data['text3_3_cost']}.")

    user1_credits_after_admin_use = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["admin_headers"]).json()).credits
    assert user1_credits_after_admin_use == user1_credits_before_admin_use, "User1's credits were affected by Admin's use of their agent."
    print(f"User1's credits ({user1_credits_after_admin_use}) correctly unaffected by Admin's action.")

# --- End of Test Section 4 ---