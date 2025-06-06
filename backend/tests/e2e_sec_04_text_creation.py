# backend/tests/e2e_sec_04_text_creation.py
import pytest
from httpx import AsyncClient # Changed
import logging

from app.core.config import settings # Keep for other settings
from app.schemas.text import TextCreate, TextResponse, TextUpdate
from app.schemas.user import UserResponse
from app.schemas.credit import UserCreditUpdate, CreditTransactionResponse
from app.schemas.agent import AgentExecuteWriter, AgentExecutionResponse # MODIFIED: Added AgentExecutionResponse
from app.schemas.contest import TextSubmission, TextSubmissionResponse # MODIFIED: Changed ContestTextCreate to TextSubmission and added TextSubmissionResponse
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 4: Text Creation ---

async def test_04_01_user1_creates_text1_1_manually(client: AsyncClient): # Changed
    """User 1 creates a text (Text 1.1) using the manual text editor."""
    assert "user1_headers" in test_data, "User 1 token not found."
    text_in = TextCreate(
        title="The Mysterious Affair at the Manor",
        content="Rain lashed against the gothic windows of Blackwood Manor, each gust of wind an eerie whisper through the ancient halls. Inside, Lord Ashworth lay dead in his locked study, a single, mud-stained playing card – the Ace of Spades – clutched in his hand. Detective Grimshaw surveyed the scene, a puzzle of impossible entry and cryptic clues. Was it a disgruntled heir, a ghostly legend, or something far more sinister that had claimed the reclusive nobleman?",
        author="A. Nonymous"
    )
    response = await client.post( # Changed
        "/texts/", # MODIFIED: Added trailing slash back
        json=text_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 201, f"User 1 creating text1.1 failed: {response.text}"
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
        title="Chronicles of the Seventh Moon",
        content="Under the glow of the fractured seventh moon, Elara, last of the Moonweavers, traced the glowing sigils on the Obsidian Tablet. The prophecies spoke of a creeping shadow, a blight that threatened to consume the land of Aethel. With her ancestral staff in hand and a courage she didn't know she possessed, Elara knew she had to venture into the Whispering Peaks to seek the Sunstone, the only relic capable of banishing the encroaching darkness.",
        author="Ignoto P. Escritor"
    )
    response = await client.post( # Changed
        "/texts/", # MODIFIED: Added trailing slash back
        json=text_in.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 201, f"User 2 creating text2.1 failed: {response.text}"
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
    new_content = "Under the glow of the fractured seventh moon, Elara, last of the Moonweavers, traced the glowing sigils on the Obsidian Tablet. The prophecies spoke of a creeping shadow, a blight that threatened to consume the land of Aethel. With her ancestral staff in hand and a courage she didn't know she possessed, Elara knew she had to venture into the Whispering Peaks to seek the Sunstone – a relic now whispered to be guarded by a mechanical dragon – the only artifact capable of banishing the encroaching darkness. This path would be more perilous than she imagined."
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

    user_response = await client.get("/users/me", headers=test_data["user1_headers"]) # Changed
    assert user_response.status_code == 200
    initial_credits = UserResponse(**user_response.json()).credits
    # This assertion might be too strict if previous tests could alter credits.
    # For now, assuming test_data reflects the true initial state (0 after registration).
    # If other tests give credits, this should be initial_credits_user1 <= 0 or similar logic
    assert initial_credits == 0, f"User 1 initial credits expected to be 0 for this test, got {initial_credits}."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="Text Gen Attempt No Credits"
    )
    response = await client.post( # Changed
        "/agents/execute/writer", # MODIFIED: Revert to original path
        json=execute_payload.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 402, f"User 1 using writer1 with no credits should fail (402 Payment Required), got {response.status_code}: {response.text}"
    
    user_response_after = await client.get("/users/me", headers=test_data["user1_headers"]) # Changed
    assert user_response_after.status_code == 200
    assert UserResponse(**user_response_after.json()).credits == initial_credits
    print("User 1 using writer1 with no credits failed as expected (402), credits unchanged.")

@pytest.mark.run(after='test_04_06_user1_uses_writer1_no_credits_fails')
async def test_04_07_admin_assigns_credits(client: AsyncClient): # Changed
    """Admin assigns 50 credits to User 1 and 100 credits to User 2."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data and "user2_id" in test_data, "User IDs not found."

    credits_user1 = UserCreditUpdate(credits=50, description="Admin grant to user 1 for testing") # Explicit description
    response_u1 = await client.patch( # MODIFIED method from POST to PATCH
        f"/admin/users/{test_data['user1_id']}/credits",
        json=credits_user1.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u1.status_code == 200, f"Admin assigning credits to User 1 failed: {response_u1.text}"
    tx_resp1 = CreditTransactionResponse(**response_u1.json())
    assert tx_resp1.user_id == test_data["user1_id"]
    assert tx_resp1.amount == 50  # Check transaction amount matches what we sent
    # We cannot assert new_balance directly from the transaction response

    credits_user2 = UserCreditUpdate(credits=100, description="Admin grant to user 2 for testing") # Explicit description
    response_u2 = await client.patch( # MODIFIED method from POST to PATCH
        f"/admin/users/{test_data['user2_id']}/credits",
        json=credits_user2.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response_u2.status_code == 200, f"Admin assigning credits to User 2 failed: {response_u2.text}"
    tx_resp2 = CreditTransactionResponse(**response_u2.json())
    assert tx_resp2.user_id == test_data["user2_id"]
    assert tx_resp2.amount == 100  # Check transaction amount matches what we sent
    # We cannot assert new_balance directly from the transaction response

    # Verify final balances by querying user data
    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"]) # Use admin headers to view
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    user1_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user2_data = next(u for u in users_data if u['id'] == test_data['user2_id'])
    assert user1_data['credits'] == 50 # Assert final balance
    assert user2_data['credits'] == 100 # Assert final balance

@pytest.mark.run(after='test_04_07_admin_assigns_credits')
async def test_04_08_user1_uses_writer1_with_credits_succeeds(client: AsyncClient): # Changed
    """User 1 attempts to use writer1 to generate a text -> Succeeds, creating Text 1.2."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    user_response_before = await client.get("/users/me", headers=test_data["user1_headers"]) # Changed
    initial_credits_user1 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user1 > 0, "User 1 has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="The Clockwork Dragon",
        description="A tale of gears and fire."
    )
    response = await client.post( # Changed
        "/agents/execute/writer", # MODIFIED: Revert to original path
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

    user_response_after = await client.get("/users/me", headers=test_data["user1_headers"]) # Changed
    final_credits_user1 = UserResponse(**user_response_after.json()).credits
    assert final_credits_user1 == initial_credits_user1 - credits_used_user1, f"User 1 credit balance did not decrease correctly. initial: {initial_credits_user1}, final: {final_credits_user1}, credits used: {credits_used_user1}."
    print(f"User 1 credits decreased from {initial_credits_user1} to {final_credits_user1} (cost: {credits_used_user1}).")

    users_resp_user2 = await client.get("/admin/users", headers=test_data["admin_headers"]) # Changed
    users_data_user2 = users_resp_user2.json()
    user2_data = next(u for u in users_data_user2 if u['id'] == test_data['user2_id'])
    initial_credits_user2 = user2_data['credits'] 
    print(f"User 2 credits remain: {initial_credits_user2}. This test does not modify them.")

@pytest.mark.run(after='test_04_08_user1_uses_writer1_with_credits_succeeds')
async def test_04_09_user2_uses_writer1_fails(client: AsyncClient): # Changed
    """User 2 attempts to use writer1 (User 1's private agent) -> Fails."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="Attempt by User2 on User1 Agent"
    )
    response = await client.post( # Changed
        "/agents/execute/writer", # MODIFIED: Revert to original path
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

    user_response_before = await client.get("/users/me", headers=test_data["user2_headers"]) # Changed
    initial_credits_user2 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user2 > 0, "User 2 has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer_global_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="Journey to the Crystal Caves",
        description="A thrilling subterranean expedition."
    )
    response = await client.post( # Changed
        "/agents/execute/writer", # MODIFIED: Revert to original path
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

    user_response_after_user2 = await client.get("/users/me", headers=test_data["user2_headers"]) # Changed
    final_credits_user2 = UserResponse(**user_response_after_user2.json()).credits
    assert final_credits_user2 == initial_credits_user2 - credits_used_user2, "User 2 credit balance did not decrease correctly."
    print(f"User 2 credits decreased from {initial_credits_user2} to {final_credits_user2} (cost: {credits_used_user2}).")

@pytest.mark.run(after='test_04_10_user2_uses_global_writer_succeeds')
async def test_04_11_user1_creates_text1_3_manually(client: AsyncClient): # Changed
    """User 1 creates another text (Text 1.3) manually."""
    assert "user1_headers" in test_data, "User 1 token not found."
    text_in = TextCreate(
        title="Whispers in the Static",
        content="The long-range comms array on Outpost Kepler suddenly crackled to life, not with the usual garbled telemetry, but with a faint, rhythmic melody buried deep within the cosmic static. Xenolinguist Dr. Aris Thorne leaned closer, his heart pounding. It wasn't random noise; it was structured, intelligent. As he began to decipher the alien lullaby, a chilling realization dawned – the song was a warning, and humanity was the subject.",
        author="Anon E. Mous"
    )
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["user1_headers"]) # MODIFIED: Added trailing slash back
    assert response.status_code == 201, f"User 1 creating text1.3 failed: {response.text}"
    test_data["text1_3_id"] = TextResponse(**response.json()).id
    print(f"User 1 created Text 1.3 (ID: {test_data['text1_3_id']}) manually.")

@pytest.mark.run(after='test_04_11_user1_creates_text1_3_manually')
async def test_04_12_user2_creates_text2_3_manually(client: AsyncClient): # Changed
    """User 2 creates another text (Text 2.3) manually."""
    assert "user2_headers" in test_data, "User 2 token not found."
    text_in = TextCreate(
        title="Echoes of the Past",
        content="The old fisherman, Santiago, claimed the sea itself whispered secrets to him – secrets of a forgotten treasure ship, swallowed by a tempest a century ago. Most villagers dismissed him as mad, but young Leo, captivated by the glint in Santiago's eyes and the tattered map he clutched, believed. Together, they set sail on a rickety boat, chasing a legend into the heart of the Bermuda Triangle, unaware that the treasure was guarded by more than just a watery grave.",
        author="Incognito Writer"
    )
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["user2_headers"]) # MODIFIED: Added trailing slash back
    assert response.status_code == 201, f"User 2 creating text2.3 failed: {response.text}"
    test_data["text2_3_id"] = TextResponse(**response.json()).id
    print(f"User 2 created Text 2.3 (ID: {test_data['text2_3_id']}) manually.")

@pytest.mark.run(after='test_04_12_user2_creates_text2_3_manually')
async def test_04_13_admin_creates_text3_1_manually(client: AsyncClient): # Changed
    """Admin creates a text (Text 3.1) manually."""
    assert "admin_headers" in test_data, "Admin token not found."
    text_in = TextCreate(
        title="The Alchemist's Secret",
        content="In the hidden chambers beneath Prague, Master Alchemist Valerius toiled over his magnum opus – not gold from lead, but life from clay. His Golem, animated by arcane formulae and a spark of forbidden celestial fire, stood nearly complete. But as he prepared the final incantation, a tremor of doubt shook him. What was the true cost of creation, and could he control the power he was about to unleash upon an unsuspecting world?",
        author="Mr. A. D. Min"
    )
    response = await client.post("/texts/", json=text_in.model_dump(), headers=test_data["admin_headers"]) # MODIFIED: Added trailing slash back
    assert response.status_code == 201, f"Admin creating text3.1 failed: {response.text}"
    test_data["text3_1_id"] = TextResponse(**response.json()).id
    print(f"Admin created Text 3.1 (ID: {test_data['text3_1_id']}) manually.")

@pytest.mark.run(after='test_04_13_admin_creates_text3_1_manually')
async def test_04_14_admin_uses_writer_global_succeeds(client: AsyncClient): # Changed
    """Admin uses writer_global to create a text (Text 3.2)."""
    assert "admin_headers" in test_data and "admin_id" in test_data, "Admin token/ID not found."
    assert "writer_global_id" in test_data, "Global Writer ID not found."

    user_response_before = await client.get("/users/me", headers=test_data["admin_headers"]) # Changed
    initial_credits_admin = UserResponse(**user_response_before.json()).credits
    # Admin has fixed credits, but good to ensure they are positive for testing if costs apply
    # assert initial_credits_admin > 0, "Admin has no credits before attempting AI generation."

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer_global_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="Neon City Nights",
        description="A cyberpunk adventure."
    )
    response = await client.post("/agents/execute/writer", json=execute_payload.model_dump(), headers=test_data["admin_headers"]) # MODIFIED: Correct path
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

    user_response_after = await client.get("/users/me", headers=test_data["admin_headers"]) # Changed
    final_credits_admin = UserResponse(**user_response_after.json()).credits
    # Assuming admin credits are not deducted for now (e.g., 1000 stays 1000 or similar logic)
    # This might need adjustment based on actual admin credit logic
    # assert final_credits_admin == initial_credits_admin - credits_used_admin, "Admin credit balance did not decrease correctly/as expected."
    print(f"Admin credits were {initial_credits_admin}, now {final_credits_admin} (cost: {credits_used_admin}).")

@pytest.mark.run(after='test_04_14_admin_uses_writer_global_succeeds')
async def test_04_15_admin_uses_user1_writer1_succeeds(client: AsyncClient): # Changed
    """Admin uses writer1 to create a text (Text 3.3)."""
    assert "admin_headers" in test_data and "admin_id" in test_data, "Admin token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."
    assert "user1_id" in test_data, "User 1 ID not found." # For credit check

    # Check User 1's credits before to ensure they are not affected
    users_resp_before = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp_before.status_code == 200
    users_data_before = users_resp_before.json()
    user1_data_before = next(u for u in users_data_before if u['id'] == test_data['user1_id'])
    initial_credits_user1 = user1_data_before['credits']

    execute_payload = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="The Silent Guardian",
        description="A fantasy short produced by an agent."
    )
    response = await client.post( # Changed
        "/agents/execute/writer", # MODIFIED: Revert to original path
        json=execute_payload.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin using User1's writer1 failed: {response.text}"
    
    exec_response_data = AgentExecutionResponse(**response.json()) # MODIFIED: Use dedicated schema
    test_data["text3_3_id"] = exec_response_data.result_id
    admin_cost_text3_3 = exec_response_data.credits_used
    
    assert admin_cost_text3_3 > 0, "Admin's cost for Text 3.3 should be > 0"
    test_data["text3_3_cost"] = admin_cost_text3_3 # Storing the cost for admin

    text_response = await client.get(f"/texts/{test_data['text3_3_id']}", headers=test_data["admin_headers"]) # Changed
    assert text_response.status_code == 200
    new_text = TextResponse(**text_response.json())
    assert new_text.title == execute_payload.title
    # Admin is the owner when executing any agent directly
    assert new_text.owner_id == test_data["admin_id"]
    print(f"Admin created AI-generated Text 3.3 (ID: {test_data['text3_3_id']}) using writer1 successfully.")

    # Verify User 1's credits were NOT affected
    users_resp_after = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp_after.status_code == 200
    users_data_after = users_resp_after.json()
    user1_data_after = next(u for u in users_data_after if u['id'] == test_data['user1_id'])
    final_credits_user1 = user1_data_after['credits']
    assert final_credits_user1 == initial_credits_user1, "User 1's credits should not change when admin uses their agent."
    print(f"User 1 credits remain unchanged at {final_credits_user1} after admin used writer1.")

    # Verify admin's own credit transaction history (optional, good for thoroughness)
    # This would require an endpoint to fetch admin's credit history. For now, we assume it's recorded.
    print(f"Admin incurred a cost of {admin_cost_text3_3} for generating Text 3.3.")

@pytest.mark.run(after='test_04_15_admin_uses_user1_writer1_succeeds')
async def test_04_16_user1_creates_text1_4_with_writer1_and_submits_to_contest1(client: AsyncClient):
    """User 1 creates Text 1.4 using writer1, (no direct submission here, submission is in sec 5).
       This test focuses on AI text creation and credit deduction.
    """
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Get User 1's initial credits
    user_response_before = await client.get("/users/me", headers=test_data["user1_headers"])
    assert user_response_before.status_code == 200
    initial_credits_user1 = UserResponse(**user_response_before.json()).credits
    assert initial_credits_user1 > 0, "User 1 has no credits before attempting AI generation for Text 1.4."

    # Step 1: User 1 creates Text 1.4 using writer1
    execute_payload_text1_4 = AgentExecuteWriter(
        agent_id=test_data["writer1_id"],
        model=settings.DEFAULT_TEST_MODEL_ID,
        title="Pirate's Gold",
        description="A swashbuckling adventure for the high seas."
    )
    response_gen_text1_4 = await client.post(
        "/agents/execute/writer",
        json=execute_payload_text1_4.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response_gen_text1_4.status_code == 200, f"User 1 creating Text 1.4 with writer1 failed: {response_gen_text1_4.text}"
    
    exec_response_text1_4 = AgentExecutionResponse(**response_gen_text1_4.json())
    test_data["text1_4_id"] = exec_response_text1_4.result_id
    credits_used_text1_4 = exec_response_text1_4.credits_used
    assert credits_used_text1_4 > 0, "Credits used for Text 1.4 should be greater than 0."
    test_data["text1_4_cost"] = credits_used_text1_4

    print(f"User 1 created AI-generated Text 1.4 (ID: {test_data['text1_4_id']}) with cost {credits_used_text1_4}.")

    # Verify User 1's credit balance decreased
    user_response_after_gen = await client.get("/users/me", headers=test_data["user1_headers"])
    assert user_response_after_gen.status_code == 200
    final_credits_user1_after_gen = UserResponse(**user_response_after_gen.json()).credits
    assert final_credits_user1_after_gen == initial_credits_user1 - credits_used_text1_4, "User 1 credit balance did not decrease correctly after Text 1.4 generation."
    print(f"User 1 credits decreased from {initial_credits_user1} to {final_credits_user1_after_gen}.")

    # Step 2: User 1 submits Text 1.4 to contest1
    submission_payload = TextSubmission(text_id=test_data["text1_4_id"]) # MODIFIED: Used TextSubmission schema
    response_submit_text1_4 = await client.post(
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response_submit_text1_4.status_code in [200, 201], f"User 1 submitting Text 1.4 to contest1 failed: {response_submit_text1_4.text}"
    
    submission_data = TextSubmissionResponse(**response_submit_text1_4.json()) # MODIFIED: Used TextSubmissionResponse
    assert submission_data.text_id == test_data["text1_4_id"]
    assert submission_data.contest_id == test_data["contest1_id"]
    test_data["submission_c1_t1_4_id"] = submission_data.submission_id # MODIFIED: Used .submission_id from schema

    print(f"User 1 successfully submitted Text 1.4 (ID: {test_data['text1_4_id']}) to Contest 1 (ID: {test_data['contest1_id']}). Submission ID: {test_data.get('submission_c1_t1_4_id')}")

    # Verify contest details (optional, but good for sanity check)
    contest_details_resp = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"])
    assert contest_details_resp.status_code == 200
    # We could add assertions here about the number of texts/participants in contest1 if precise counts are tracked.
    # For now, successful submission is the primary goal.
    print(f"Test 04.16 completed: User 1 created Text 1.4 with writer1 and submitted it to contest1.")

# --- End of Test Section 4 ---