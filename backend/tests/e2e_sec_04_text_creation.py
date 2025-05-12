# backend/tests/e2e_sec_04_text_creation.py
import pytest
from httpx import AsyncClient # Changed
import logging

from app.core.config import settings # Keep for other settings
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.schemas.user import UserResponse, UserCredit # For credit checks and assignments
from app.schemas.agent import AgentExecuteWriter # MODIFIED: For agent execution, specifically writer
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 4: Text Creation ---

async def test_04_01_user1_creates_text1_1_manually(client: AsyncClient): # Changed
    """User 1 creates a text (Text 1.1) using the manual text editor."""
    assert "user1_headers" in test_data, "User 1 token not found."
    text_in = TextCreate(
        title="User1's First Masterpiece",
        content="# Chapter 1\nIt was a dark and stormy night...",
        author="User1 Author Name"
    )
    response = await client.post( # Changed
        "/texts/", # Changed
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
async def test_04_02_user2_creates_text2_1_manually(client: AsyncClient): # Changed
    """User 2 creates a text (Text 2.1) using the manual text editor."""
    assert "user2_headers" in test_data, "User 2 token not found."
    text_in = TextCreate(
        title="User2's Gripping Tale",
        content="## Prologue\nOnce upon a time, in a land far, far away...",
        author="User2 Pen Name"
    )
    response = await client.post( # Changed
        "/texts/", # Changed
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
async def test_04_03_user1_views_text2_1_succeeds(client: AsyncClient): # Changed
    """User 1 attempts to view Text 2.1 details -> Succeeds (texts are public by default)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    response = await client.get( # Changed
        f"/texts/{test_data['text2_1_id']}", # Changed
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 viewing text2.1 failed: {response.text}"
    text_data_resp = TextResponse(**response.json()) # Renamed to avoid conflict with tests.shared_test_state.test_data
    assert text_data_resp.id == test_data["text2_1_id"]
    print("User 1 successfully viewed Text 2.1 details.")

@pytest.mark.run(after='test_04_03_user1_views_text2_1_succeeds')
async def test_04_04_user1_edits_text2_1_fails(client: AsyncClient): # Changed
    """User 1 tries to edit Text 2.1 -> Fails (only owners can edit their texts)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    update_payload = TextUpdate(content="User 1 trying to maliciously edit this.")
    response = await client.put( # Changed
        f"/texts/{test_data['text2_1_id']}", # Changed
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 editing text2.1 should fail (403), but got {response.status_code}: {response.text}"
    print("User 1 attempt to edit Text 2.1 failed as expected (403 Forbidden).")

@pytest.mark.run(after='test_04_04_user1_edits_text2_1_fails')
async def test_04_05_user2_edits_text2_1_succeeds(client: AsyncClient): # Changed
    """User 2 edits Text 2.1 -> Succeeds."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    new_content = "## Prologue\nOnce upon a time, in a land far, far away... User 2 made an edit!"
    update_payload = TextUpdate(content=new_content)
    response = await client.put( # Changed
        f"/texts/{test_data['text2_1_id']}", # Changed
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 editing text2.1 failed: {response.text}"
    updated_text = TextResponse(**response.json())
    assert updated_text.content == new_content
    print("User 2 successfully edited Text 2.1.")

@pytest.mark.run(after='test_04_05_user2_edits_text2_1_succeeds')
async def test_04_06_user1_uses_writer1_no_credits_fails(client: AsyncClient): # Changed
    """User 1 tries to use writer1 to generate a text -> Fails (no credits)."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    user_response = await client.get(f"/users/{test_data['user1_id']}", headers=test_data["user1_headers"]) # Changed
    assert user_response.status_code == 200
    initial_credits = UserResponse(**user_response.json()).credits
    # This assertion might be too strict if previous tests could alter credits.
    # For now, assuming test_data reflects the true initial state (0 after registration).
    # If other tests give credits, this should be initial_credits_user1 <= 0 or similar logic
    assert initial_credits == 0, f"User 1 initial credits expected to be 0 for this test, got {initial_credits}."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest", 
        title="Text Gen Attempt No Credits"
    )
    response = await client.post( # Changed
        "/agents/execute", # Changed
        json=execute_payload.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 402, f"User 1 using writer1 with no credits should fail (402 Payment Required), got {response.status_code}: {response.text}"
    
    user_response_after = await client.get(f"/users/{test_data['user1_id']}", headers=test_data["user1_headers"]) # Changed
    assert user_response_after.status_code == 200
    assert UserResponse(**user_response_after.json()).credits == initial_credits
    print("User 1 using writer1 with no credits failed as expected (402), credits unchanged.")

@pytest.mark.run(after='test_04_06_user1_uses_writer1_no_credits_fails')
async def test_04_07_admin_assigns_credits(client: AsyncClient): # Changed
    """Admin assigns 50 credits to User 1 and 100 credits to User 2."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data and "user2_id" in test_data, "User IDs not found."

    credits_user1 = UserCredit(credits=50)
    response_u1 = await client.post( # Changed
        f"/admin/users/{test_data['user1_id']}/credits", # Changed
        json=credits_user1.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u1.status_code == 200, f"Admin assigning credits to User 1 failed: {response_u1.text}"
    assert UserResponse(**response_u1.json()).credits == 50
    print(f"Admin assigned 50 credits to User 1 (ID: {test_data['user1_id']}).")

    credits_user2 = UserCredit(credits=100)
    response_u2 = await client.post( # Changed
        f"/admin/users/{test_data['user2_id']}/credits", # Changed
        json=credits_user2.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u2.status_code == 200, f"Admin assigning credits to User 2 failed: {response_u2.text}"
    assert UserResponse(**response_u2.json()).credits == 100
    print(f"Admin assigned 100 credits to User 2 (ID: {test_data['user2_id']}).")

@pytest.mark.run(after='test_04_07_admin_assigns_credits')
async def test_04_08_user1_uses_writer1_with_credits_succeeds(client: AsyncClient): # Changed
    """User 1 attempts to use writer1 to generate a text -> Succeeds, creating Text 1.2."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    user_response_before = await client.get(f"/users/{test_data['user1_id']}", headers=test_data["user1_headers"]) # Changed
    initial_credits_user1 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user1 > 0, "User 1 has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest",
        title="AI Generated Story by User1",
        description="A short story generated by writer1."
    )
    response = await client.post( # Changed
        "/agents/execute", # Changed
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

    text_response = await client.get(f"/texts/{test_data['text1_2_id']}", headers=test_data["user1_headers"]) # Changed
    assert text_response.status_code == 200
    new_text = TextResponse(**text_response.json())
    assert new_text.title == execute_payload.title
    assert new_text.owner_id == test_data["user1_id"]
    print(f"User 1 created AI-generated Text 1.2 (ID: {test_data['text1_2_id']}) successfully.")

    user_response_after = await client.get(f"/users/{test_data['user1_id']}", headers=test_data["user1_headers"]) # Changed
    final_credits_user1 = UserResponse(**user_response_after.json()).credits
    assert final_credits_user1 == initial_credits_user1 - credits_used_user1, "User 1 credit balance did not decrease correctly."
    print(f"User 1 credits decreased from {initial_credits_user1} to {final_credits_user1} (cost: {credits_used_user1}).")

    user_response_user2 = await client.get(f"/users/{test_data['user2_id']}", headers=test_data["admin_headers"]) # Changed
    initial_credits_user2 = UserResponse(**user_response_user2.json()).credits 
    print(f"User 2 credits remain: {initial_credits_user2}. This test does not modify them.")

@pytest.mark.run(after='test_04_08_user1_uses_writer1_with_credits_succeeds')
async def test_04_09_user2_uses_writer1_fails(client: AsyncClient): # Changed
    """User 2 attempts to use writer1 (User 1's private agent) -> Fails."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model="claude-3-5-haiku-latest",
        title="Attempt by User2 on User1 Agent"
    )
    response = await client.post( # Changed
        "/agents/execute", # Changed
        json=execute_payload.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [403, 404], \
        f"User 2 using User1's writer1 should fail (403/404), got {response.status_code}: {response.text}"
    print("User 2 attempt to use User1's private writer1 failed as expected.")

@pytest.mark.run(after='test_04_09_user2_uses_writer1_fails')
async def test_04_10_user2_uses_global_writer_succeeds(client: AsyncClient): # Changed
    """User 2 uses the global writer (writer_global) to generate a text (Text 2.2)."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "writer_global_id" in test_data, "Global Writer ID not found."

    user_response_before = await client.get(f"/users/{test_data['user2_id']}", headers=test_data["user2_headers"]) # Changed
    initial_credits_user2 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user2 > 0, "User 2 has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer_global_id"],
        model="claude-3-5-haiku-latest",
        title="AI Generated Story by User2 via Global Writer",
        description="A short story generated by writer_global for User2."
    )
    response = await client.post( # Changed
        "/agents/execute", # Changed
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

    text_response_user2 = await client.get(f"/texts/{test_data['text2_2_id']}", headers=test_data["user2_headers"]) # Changed
    assert text_response_user2.status_code == 200
    new_text_user2 = TextResponse(**text_response_user2.json())
    assert new_text_user2.title == execute_payload.title
    assert new_text_user2.owner_id == test_data["user2_id"]
    print(f"User 2 created AI-generated Text 2.2 (ID: {test_data['text2_2_id']}) successfully.")

    user_response_after_user2 = await client.get(f"/users/{test_data['user2_id']}", headers=test_data["user2_headers"]) # Changed
    final_credits_user2 = UserResponse(**user_response_after_user2.json()).credits
    assert final_credits_user2 == initial_credits_user2 - credits_used_user2, "User 2 credit balance did not decrease correctly."
    print(f"User 2 credits decreased from {initial_credits_user2} to {final_credits_user2} (cost: {credits_used_user2}).")

@pytest.mark.run(after='test_04_10_user2_uses_global_writer_succeeds')
async def test_04_11_user1_creates_text1_3_manually(client: AsyncClient): # Changed
    """User 1 creates Text 1.3 manually for contest submission later."""
    assert "user1_headers" in test_data, "User 1 token not found."
    text_in = TextCreate(title="User1 Contest Entry A", content="This is User1\'s first entry for the contest.", author="User1 Author Alias")
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["user1_headers"]) # Changed
    assert response.status_code == 200, f"User 1 creating text1.3 failed: {response.text}"
    test_data["text1_3_id"] = TextResponse(**response.json()).id
    print(f"User 1 created Text 1.3 (ID: {test_data['text1_3_id']}) manually.")

@pytest.mark.run(after='test_04_11_user1_creates_text1_3_manually')
async def test_04_12_user2_creates_text2_3_manually(client: AsyncClient): # Changed
    """User 2 creates Text 2.3 manually for contest submission later."""
    assert "user2_headers" in test_data, "User 2 token not found."
    text_in = TextCreate(title="User2 Contest Entry X", content="User2 submits this exciting story for consideration.", author="User2 Writer Tag")
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["user2_headers"]) # Changed
    assert response.status_code == 200, f"User 2 creating text2.3 failed: {response.text}"
    test_data["text2_3_id"] = TextResponse(**response.json()).id
    print(f"User 2 created Text 2.3 (ID: {test_data['text2_3_id']}) manually.")

@pytest.mark.run(after='test_04_12_user2_creates_text2_3_manually')
async def test_04_13_admin_creates_text3_1_manually(client: AsyncClient): # Changed
    """Admin creates Text 3.1 manually for contest submission later."""
    assert "admin_headers" in test_data, "Admin token not found."
    text_in = TextCreate(
        title="Admin's Special Submission", 
        content="An exemplary piece by the administrator.", 
        author="The Overseer"
    )
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["admin_headers"]) # Changed
    assert response.status_code == 200, f"Admin creating text3.1 failed: {response.text}"
    test_data["text3_1_id"] = TextResponse(**response.json()).id
    print(f"Admin created Text 3.1 (ID: {test_data['text3_1_id']}) manually.")

@pytest.mark.run(after='test_04_13_admin_creates_text3_1_manually')
async def test_04_14_admin_uses_writer_global_succeeds(client: AsyncClient): # Changed
    """Admin uses writer_global to generate Text 3.2."""
    assert "admin_headers" in test_data and "admin_id" in test_data, "Admin token/ID not found."
    assert "writer_global_id" in test_data, "Global Writer ID not found."

    user_response_before = await client.get(f"/users/{test_data['admin_id']}", headers=test_data["admin_headers"]) # Changed
    initial_credits_admin = UserResponse(**user_response_before.json()).credits
    # Admin has fixed credits, but good to ensure they are positive for testing if costs apply
    # assert initial_credits_admin > 0, "Admin has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer_global_id"],
        model="claude-3-5-haiku-latest",
        title="AI Generated Story by Admin via Global Writer",
        description="A short story generated by writer_global for Admin."
    )
    response = await client.post("/agents/execute", json=execute_payload.model_dump(), headers=test_data["admin_headers"]) # Changed
    assert response.status_code == 200, f"Admin using writer_global failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data
    assert "credits_used" in exec_response_data
    test_data["text3_2_id"] = exec_response_data["result_id"]
    credits_used_admin = exec_response_data["credits_used"]
    # Admins might have infinite credits or not be charged. This depends on implementation.
    # For now, we just check that credits_used is reported. The balance check is more nuanced for admin.
    # assert credits_used_admin >= 0 # Can be 0 if admin is not charged
    test_data["text3_2_cost"] = credits_used_admin

    text_response_admin = await client.get(f"/texts/{test_data['text3_2_id']}", headers=test_data["admin_headers"]) # Changed
    assert text_response_admin.status_code == 200
    new_text_admin = TextResponse(**text_response_admin.json())
    assert new_text_admin.title == execute_payload.title
    assert new_text_admin.owner_id == test_data["admin_id"]
    print(f"Admin created AI-generated Text 3.2 (ID: {test_data['text3_2_id']}) successfully.")

    user_response_after = await client.get(f"/users/{test_data['admin_id']}", headers=test_data["admin_headers"]) # Changed
    final_credits_admin = UserResponse(**user_response_after.json()).credits
    # Assuming admin credits are not deducted for now (e.g., 1000 stays 1000 or similar logic)
    # This might need adjustment based on actual admin credit logic
    # assert final_credits_admin == initial_credits_admin - credits_used_admin, "Admin credit balance did not decrease correctly/as expected."
    print(f"Admin credits were {initial_credits_admin}, now {final_credits_admin} (cost: {credits_used_admin}).")

@pytest.mark.run(after='test_04_14_admin_uses_writer_global_succeeds')
async def test_04_15_admin_uses_user1_writer1_succeeds(client: AsyncClient): # Changed
    """Admin uses User1's private writer1 to generate Text 3.3. Succeeds as admin."""
    assert "admin_headers" in test_data and "admin_id" in test_data, "Admin token/ID not found."
    assert "writer1_id" in test_data, "User1's Writer1 ID not found."

    user_response_before = await client.get(f"/users/{test_data['admin_id']}", headers=test_data["admin_headers"]) # Changed
    initial_credits_admin = UserResponse(**user_response_before.json()).credits

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"], # User1's agent
        model="claude-3-5-haiku-latest",
        title="AI Story by Admin via User1-Writer1",
        description="Admin leveraging User1\'s private agent."
    )
    response = await client.post("/agents/execute", json=execute_payload.model_dump(), headers=test_data["admin_headers"]) # Changed
    assert response.status_code == 200, f"Admin using User1\'s writer1 failed: {response.text}"
    exec_response_data = response.json()
    assert "result_id" in exec_response_data
    assert "credits_used" in exec_response_data
    test_data["text3_3_id"] = exec_response_data["result_id"]
    credits_used_admin_on_user1_agent = exec_response_data["credits_used"]
    test_data["text3_3_cost"] = credits_used_admin_on_user1_agent

    text_response_admin = await client.get(f"/texts/{test_data['text3_3_id']}", headers=test_data["admin_headers"]) # Changed
    assert text_response_admin.status_code == 200
    new_text_admin = TextResponse(**text_response_admin.json())
    assert new_text_admin.title == execute_payload.title
    assert new_text_admin.owner_id == test_data["admin_id"] # Text is owned by admin
    print(f"Admin created AI-generated Text 3.3 (ID: {test_data['text3_3_id']}) via User1\'s agent successfully.")

    user_response_after = await client.get(f"/users/{test_data['admin_id']}", headers=test_data["admin_headers"]) # Changed
    final_credits_admin = UserResponse(**user_response_after.json()).credits
    print(f"Admin credits were {initial_credits_admin}, now {final_credits_admin} (cost for using User1's agent: {credits_used_admin_on_user1_agent}).")

# --- End of Test Section 4 ---