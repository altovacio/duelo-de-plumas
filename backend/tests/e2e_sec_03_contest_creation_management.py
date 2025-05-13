# backend/tests/e2e_sec_03_contest_creation_management.py
import pytest
from httpx import AsyncClient # Changed
from app.core.config import settings # Keep for other settings
from app.schemas.contest import ContestCreate, ContestResponse, ContestUpdate
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 3: Contest Creation & Management ---

async def test_03_01_user1_creates_public_contest1_and_assigns_judge(client: AsyncClient): # Changed
    """User 1 creates a public Contest (contest1) and assigns judge_global."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "judge_global_id" in test_data, "Global Judge ID not found."

    contest_in = ContestCreate(
        title="User1's First Public Contest",
        description="An exciting contest open to all great writers!",
        is_private=False,
        judge_restrictions=False,
        owner_restrictions=False
    )
    response = await client.post( # Changed
        "/contests/", # Changed
        json=contest_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 201, f"User 1 creating contest1 failed: {response.text}"
    assert "id" in response.json(), "Contest ID not in response after creation."
    contest1_data = ContestResponse(**response.json())
    assert contest1_data.title == contest_in.title
    assert not contest1_data.is_private
    assert contest1_data.creator_id == test_data["user1_id"]
    test_data["contest1_id"] = contest1_data.id
    print(f"User 1 created public contest1 (ID: {test_data['contest1_id']}) successfully.")

    assign_judge_payload = {"agent_id": test_data["judge_global_id"]}
    response_assign_judge = await client.post( # Changed
        f"/contests/{test_data['contest1_id']}/judges", # Path was already correct relative to /contests/
        json=assign_judge_payload,
        headers=test_data["user1_headers"]
    )
    assert response_assign_judge.status_code in [200, 201], \
        f"User 1 assigning judge_global to contest1 failed: {response_assign_judge.text}"
    print(f"User 1 assigned judge_global (ID: {test_data['judge_global_id']}) to contest1 successfully.")

@pytest.mark.run(after='test_03_01_user1_creates_public_contest1_and_assigns_judge')
async def test_03_02_admin_creates_private_contest2_and_assigns_judges(client: AsyncClient): # Changed
    """Admin creates a private Contest (contest2) with restrictions and assigns judges."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."
    assert "judge_global_id" in test_data, "Global Judge ID not found."

    test_data["contest2_password"] = "securePa$$wOrd"
    contest_in = ContestCreate(
        title="Admin's Super Secret Private Contest",
        description="Only for the elite! Strict rules apply.",
        is_private=True,
        password=test_data["contest2_password"],
        judge_restrictions=True,
        author_restrictions=True
    )
    response = await client.post( # Changed
        "/contests/", # Changed
        json=contest_in.model_dump(exclude_none=True),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 201, f"Admin creating contest2 failed: {response.text}"
    contest2_data = ContestResponse(**response.json())
    assert contest2_data.title == contest_in.title
    assert contest2_data.is_private
    assert contest2_data.creator_id == test_data["admin_id"]
    test_data["contest2_id"] = contest2_data.id
    print(f"Admin created private contest2 (ID: {test_data['contest2_id']}) successfully.")

    judges_to_assign = [
        {"user_id": test_data["user2_id"]},
        {"agent_id": test_data["judge1_id"]},
        {"agent_id": test_data["judge_global_id"]}
    ]
    for judge_payload in judges_to_assign:
        assign_judge_response = await client.post( # Changed
            f"/contests/{test_data['contest2_id']}/judges", # Path was already correct
            json=judge_payload,
            headers=test_data["admin_headers"]
        )
        judge_id_key = "user_id" if "user_id" in judge_payload else "agent_id"
        judge_id_value = judge_payload[judge_id_key]

        if judge_id_key == "agent_id" and judge_id_value == test_data["judge1_id"]:
            assert assign_judge_response.status_code == 403, \
                f"Admin assigning user1's private judge1 (ID: {judge_id_value}) should fail (403), but got {assign_judge_response.status_code}: {assign_judge_response.text}"
            print(f"Admin failed to assign user1's private judge1 (ID: {judge_id_value}) to contest2 as expected (403).")
        else:
            assert assign_judge_response.status_code in [200, 201], \
                f"Admin assigning judge {judge_payload} to contest2 failed: {assign_judge_response.text}"
            print(f"Admin assigned judge (ID: {judge_id_value}) to contest2 successfully.")

@pytest.mark.run(after='test_03_02_admin_creates_private_contest2_and_assigns_judges')
async def test_03_03_user2_creates_contest3(client: AsyncClient): # Changed
    """User 2 creates a contest (contest3) with no judges assigned. Succeeds."""
    assert "user2_headers" in test_data, "User 2 token not found."
    contest_in = ContestCreate(
        title="User2's Casual Contest",
        description="A fun contest, no pressure!",
        is_private=False
    )
    response = await client.post( # Changed
        "/contests/", # Changed
        json=contest_in.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 201, f"User 2 creating contest3 failed: {response.text}"
    contest3_data = ContestResponse(**response.json())
    assert contest3_data.title == contest_in.title
    assert contest3_data.creator_id == test_data["user2_id"]
    test_data["contest3_id"] = contest3_data.id
    print(f"User 2 created public contest3 (ID: {test_data['contest3_id']}) successfully.")

@pytest.mark.run(after='test_03_03_user2_creates_contest3')
async def test_03_04_user2_attempts_edit_contest1_fails(client: AsyncClient): # Changed
    """User 2 attempts to edit contest1 -> Should fail."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    update_payload = ContestUpdate(description="User 2 trying to change this.")
    response = await client.put( # Changed
        f"/contests/{test_data['contest1_id']}", # Changed
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 editing contest1 should fail (403), but got {response.status_code}: {response.text}"
    print("User 2 attempt to edit contest1 failed as expected (403 Forbidden).")

@pytest.mark.run(after='test_03_04_user2_attempts_edit_contest1_fails')
async def test_03_05_user1_edits_contest1_succeeds(client: AsyncClient): # Changed
    """User 1 edits contest1 (updates description). Verify success."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    new_description = "User 1 has updated the description for this exciting contest!"
    update_payload = ContestUpdate(description=new_description)
    response = await client.put( # Changed
        f"/contests/{test_data['contest1_id']}", # Changed
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 editing contest1 failed: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.description == new_description
    print(f"User 1 successfully edited contest1 description. New state: {updated_contest.state}.")

@pytest.mark.run(after='test_03_05_user1_edits_contest1_succeeds')
async def test_03_06_admin_edits_contest3_succeeds(client: AsyncClient): # Changed
    """Admin edits contest3 (updates description). Verify success."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    new_description_admin = "Admin has updated the description for User 2's contest."
    update_payload = ContestUpdate(description=new_description_admin)
    response = await client.put( # Changed
        f"/contests/{test_data['contest3_id']}", # Changed
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin editing contest3 failed: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.description == new_description_admin
    print(f"Admin successfully edited contest3 description. New state: {updated_contest.state}.")

@pytest.mark.run(after='test_03_06_admin_edits_contest3_succeeds')
async def test_03_07_user2_assign_judge1_to_contest3_fails(client: AsyncClient): # Changed
    """User 2 attempts to assign judge1 (User 1's AI agent) to contest3 (User 2's contest). Fails."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."
    
    assign_payload = {"agent_id": test_data["judge1_id"]}
    response = await client.post( # Changed
        f"/contests/{test_data['contest3_id']}/judges", # Path was already correct
        json=assign_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [403, 404], \
        f"User 2 assigning User1's judge1 to contest3 should fail (403/404), but got {response.status_code}: {response.text}"
    print("User 2 attempting to assign User1's judge1 to contest3 failed as expected.")

@pytest.mark.run(after='test_03_07_user2_assign_judge1_to_contest3_fails')
async def test_03_08_user1_assign_judge1_to_contest3_fails(client: AsyncClient): # Changed
    """User 1 attempts to assign judge1 (their AI agent) to contest3 (User 2's contest). Fails."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."

    assign_payload = {"agent_id": test_data["judge1_id"]}
    response = await client.post( # Changed
        f"/contests/{test_data['contest3_id']}/judges", # Path was already correct
        json=assign_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, \
        f"User 1 assigning judge1 to User2's contest3 should fail (403), but got {response.status_code}: {response.text}"
    print("User 1 attempting to assign judge1 to User2's contest3 failed as expected.")

@pytest.mark.run(after='test_03_08_user1_assign_judge1_to_contest3_fails')
async def test_03_09_user1_assign_self_as_judge_to_contest3_fails(client: AsyncClient): # Changed
    """User 1 attempts to assign user 1 (self) as a judge to contest3 (User 2's contest). Fails."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    assign_payload = {"user_id": test_data["user1_id"]}
    response = await client.post( # Changed
        f"/contests/{test_data['contest3_id']}/judges", # Path was already correct
        json=assign_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, \
        f"User 1 assigning self to User2's contest3 should fail (403), but got {response.status_code}: {response.text}"
    print("User 1 attempting to assign self as judge to User2's contest3 failed as expected.")

@pytest.mark.run(after='test_03_09_user1_assign_self_as_judge_to_contest3_fails')
async def test_03_10_user1_assigns_judges_to_contest1_succeeds(client: AsyncClient): # Changed
    """User 1 attempts to assign judge1 (own AI) and user 2 (human) as judges to contest1 (own). Succeeds."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."
    assert "user2_id" in test_data, "User 2 ID not found."

    payload_ai = {"agent_id": test_data["judge1_id"]}
    response_ai = await client.post( # Changed
        f"/contests/{test_data['contest1_id']}/judges", # Path was already correct
        json=payload_ai,
        headers=test_data["user1_headers"]
    )
    assert response_ai.status_code in [200, 201], f"User 1 assigning own judge1 to contest1 failed: {response_ai.text}"
    print(f"User 1 assigned own AI judge1 (ID: {test_data['judge1_id']}) to contest1 successfully.")

    payload_human = {"user_id": test_data["user2_id"]}
    response_human = await client.post( # Changed
        f"/contests/{test_data['contest1_id']}/judges", # Path was already correct
        json=payload_human,
        headers=test_data["user1_headers"]
    )
    assert response_human.status_code in [200, 201], f"User 1 assigning User 2 as judge to contest1 failed: {response_human.text}"
    print(f"User 1 assigned User 2 (ID: {test_data['user2_id']}) as human judge to contest1 successfully.")

@pytest.mark.run(after='test_03_10_user1_assigns_judges_to_contest1_succeeds')
async def test_03_11_user2_assigns_self_as_judge_to_contest3_succeeds(client: AsyncClient): # Changed
    """User 2 attempts to assign user 2 (self) as a judge to contest3 (own). Succeeds."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    assign_payload = {"user_id": test_data["user2_id"]}
    response = await client.post( # Changed
        f"/contests/{test_data['contest3_id']}/judges", # Path was already correct
        json=assign_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 assigning self as judge to contest3 failed: {response.text}"
    print(f"User 2 assigned self (ID: {test_data['user2_id']}) as human judge to contest3 successfully.")

@pytest.mark.run(after='test_03_11_user2_assigns_self_as_judge_to_contest3_succeeds')
async def test_03_12_visitor_lists_contests(client: AsyncClient): # Changed
    """Visitor lists contests -> Should see ALL contests listed."""
    response = await client.get("/contests/") # Changed
    # Expect 200 OK now
    assert response.status_code == 200, f"Visitor listing contests failed: {response.text}"
    contests = [ContestResponse(**c) for c in response.json()]
    
    # Visitor should see ALL contests (public and private) in the list
    contest_ids_visible = {c.id for c in contests}
    assert test_data["contest1_id"] in contest_ids_visible, "Contest 1 not visible to visitor."
    assert test_data["contest2_id"] in contest_ids_visible, "Contest 2 (private) not visible to visitor in list."
    assert test_data["contest3_id"] in contest_ids_visible, "Contest 3 not visible to visitor."
    print("Visitor listed contests successfully, saw all contests (public and private). ")

@pytest.mark.run(after='test_03_12_visitor_lists_contests')
async def test_03_13_user1_lists_contests(client: AsyncClient): # Changed
    """User 1 lists contests -> Should see ALL contests listed."""
    assert "user1_headers" in test_data, "User 1 token not found."
    response = await client.get("/contests/", headers=test_data["user1_headers"]) # Changed
    assert response.status_code == 200, f"User 1 listing contests failed: {response.text}"
    contests = [ContestResponse(**c) for c in response.json()]

    contest_ids_visible = {c.id for c in contests}
    # User 1 should also see ALL contests (public and private) in the list view.
    # Access control for private details is handled elsewhere (GET /{id}).
    assert test_data["contest1_id"] in contest_ids_visible, "Contest 1 not visible to User 1."
    assert test_data["contest2_id"] in contest_ids_visible, "Contest 2 (private) not visible to User 1 in list."
    assert test_data["contest3_id"] in contest_ids_visible, "Contest 3 not visible to User 1."
    # assert test_data["contest2_id"] not in contest_ids_visible, "Contest 2 (other, private) should not be visible to User 1."
    print("User 1 listed contests successfully, saw all contests (public and private).")

@pytest.mark.run(after='test_03_13_user1_lists_contests')
async def test_03_14_visitor_view_contest2_details_wrong_password_fails(client: AsyncClient): # Changed
    """Visitor attempts to view contest2 (private) with wrong password. Fails."""
    response = await client.get(f"/contests/{test_data['contest2_id']}?password=wrongpassword") # Changed
    assert response.status_code == 403, f"Viewing contest2 with wrong password should fail (403), got {response.status_code}: {response.text}"
    print("Visitor failed to view contest2 with wrong password, as expected.")

@pytest.mark.run(after='test_03_14_visitor_view_contest2_details_wrong_password_fails')
async def test_03_15_visitor_view_contest2_details_correct_password_succeeds(client: AsyncClient): # Changed
    """Visitor attempts to view contest2 (private) with correct password. Succeeds."""
    response = await client.get(f"/contests/{test_data['contest2_id']}?password={test_data['contest2_password']}") # Changed
    assert response.status_code == 200, f"Viewing contest2 with correct password failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.id == test_data["contest2_id"]
    print("Visitor viewed contest2 with correct password successfully.")

@pytest.mark.run(after='test_03_15_visitor_view_contest2_details_correct_password_succeeds')
async def test_03_16_user1_view_contest2_details_wrong_password_fails(client: AsyncClient): # Changed
    """User 1 (logged in) attempts to view contest2 (private, not owner) with wrong password. Fails."""
    assert "user1_headers" in test_data
    response = await client.get( # Changed
        f"/contests/{test_data['contest2_id']}?password=anotherwrongpassword",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 viewing contest2 with wrong password should fail (403), got {response.status_code}: {response.text}"
    print("User 1 failed to view contest2 (not owner) with wrong password, as expected.")


@pytest.mark.run(after='test_03_16_user1_view_contest2_details_wrong_password_fails')
async def test_03_17_user1_view_contest2_details_correct_password_succeeds(client: AsyncClient): # Changed
    """User 1 (logged in) attempts to view contest2 (private, not owner) with correct password. Succeeds."""
    assert "user1_headers" in test_data
    response = await client.get( # Changed
        f"/contests/{test_data['contest2_id']}?password={test_data['contest2_password']}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 viewing contest2 with correct password failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.id == test_data["contest2_id"]
    print("User 1 viewed contest2 (not owner) with correct password successfully.")

@pytest.mark.run(after='test_03_17_user1_view_contest2_details_correct_password_succeeds')
async def test_03_18_admin_view_contest2_details_no_password_succeeds(client: AsyncClient): # Changed
    """Admin (owner) attempts to view contest2 (private, owner) without password. Succeeds."""
    assert "admin_headers" in test_data
    response = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # Changed
    assert response.status_code == 200, f"Admin (owner) viewing contest2 without password failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.id == test_data["contest2_id"]
    print("Admin (owner) viewed contest2 without password successfully.")


# --- End of Test Section 3 ---