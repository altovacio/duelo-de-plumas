# backend/tests/e2e_sec_03_contest_creation_management.py
import pytest
from httpx import AsyncClient # Changed
from app.core.config import settings # Keep for other settings
from app.schemas.contest import ContestCreate, ContestResponse, ContestUpdate
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 3: Contest Creation & Management ---

async def test_03_01_user1_creates_publicly_listed_contest1_and_assigns_judge(client: AsyncClient): # Changed
    """User 1 creates a publicly listed Contest (contest1) and assigns judge_global."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "judge_global_id" in test_data, "Global Judge ID not found."

    contest_in = ContestCreate(
        title="User1's First Publicly Listed Contest",
        description="An exciting contest open to all great writers!",
        password_protected=False,
        publicly_listed=True,
        judge_restrictions=False,
        author_restrictions=False
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
    assert not contest1_data.password_protected
    assert contest1_data.publicly_listed
    assert contest1_data.creator.id == test_data["user1_id"]
    test_data["contest1_id"] = contest1_data.id
    print(f"User 1 created publicly listed contest1 (ID: {test_data['contest1_id']}) successfully.")

    assign_judge_payload = {"agent_judge_id": test_data["judge_global_id"]}
    response_assign_judge = await client.post( # Changed
        f"/contests/{test_data['contest1_id']}/judges", # Path was already correct relative to /contests/
        json=assign_judge_payload,
        headers=test_data["user1_headers"]
    )
    assert response_assign_judge.status_code in [200, 201], \
        f"User 1 assigning judge_global to contest1 failed: {response_assign_judge.text}"
    print(f"User 1 assigned judge_global (ID: {test_data['judge_global_id']}) to contest1 successfully.")

@pytest.mark.run(after='test_03_01_user1_creates_publicly_listed_contest1_and_assigns_judge')
async def test_03_02_admin_creates_publicly_listed_password_protected_contest2_and_assigns_judges(client: AsyncClient): # Changed
    """Admin creates a publicly listed password-protected Contest (contest2) with restrictions and assigns judges."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."
    assert "judge_global_id" in test_data, "Global Judge ID not found."

    test_data["contest2_password"] = "securePa$$wOrd"
    contest_in = ContestCreate(
        title="Admin's Publicly Listed Password-Protected Contest",
        description="Publicly listed but password protected! Strict rules apply.",
        password_protected=True,
        password=test_data["contest2_password"],
        publicly_listed=True,  # Changed from False to True
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
    assert contest2_data.password_protected
    assert contest2_data.publicly_listed  # Changed from not to assert
    assert contest2_data.creator.id == test_data["admin_id"]
    test_data["contest2_id"] = contest2_data.id
    print(f"Admin created publicly listed password-protected contest2 (ID: {test_data['contest2_id']}) successfully.")

    judges_to_assign = [
        {"user_judge_id": test_data["user2_id"]},
        {"agent_judge_id": test_data["judge1_id"]},
        {"agent_judge_id": test_data["judge_global_id"]}
    ]
    for judge_payload in judges_to_assign:
        assign_judge_response = await client.post( # Changed
            f"/contests/{test_data['contest2_id']}/judges", # Path was already correct
            json=judge_payload,
            headers=test_data["admin_headers"]
        )
        judge_id_key = "user_judge_id" if "user_judge_id" in judge_payload else "agent_judge_id"
        judge_id_value = judge_payload[judge_id_key]

        if judge_id_key == "agent_judge_id" and judge_id_value == test_data["judge1_id"]:
            assert assign_judge_response.status_code == 403, \
                f"Admin assigning user1's private judge1 (ID: {judge_id_value}) should fail (403), but got {assign_judge_response.status_code}: {assign_judge_response.text}"
            print(f"Admin failed to assign user1's private judge1 (ID: {judge_id_value}) to contest2 as expected (403).")
        else:
            assert assign_judge_response.status_code in [200, 201], \
                f"Admin assigning judge {judge_payload} to contest2 failed: {assign_judge_response.text}"
            print(f"Admin assigned judge (ID: {judge_id_value}) to contest2 successfully.")

@pytest.mark.run(after='test_03_02_admin_creates_publicly_listed_password_protected_contest2_and_assigns_judges')
async def test_03_03_user2_creates_contest3(client: AsyncClient): # Changed
    """User 2 creates a contest (contest3) with no judges assigned. Succeeds."""
    assert "user2_headers" in test_data, "User 2 token not found."
    contest_in = ContestCreate(
        title="User2's Casual Contest",
        description="A fun contest, no pressure!",
        password_protected=False,
        publicly_listed=True
    )
    response = await client.post( # Changed
        "/contests/", # Changed
        json=contest_in.model_dump(),
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 201, f"User 2 creating contest3 failed: {response.text}"
    contest3_data = ContestResponse(**response.json())
    assert contest3_data.title == contest_in.title
    assert contest3_data.creator.id == test_data["user2_id"]
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
    print(f"User 1 successfully edited contest1 description. New status: {updated_contest.status}.")

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
    print(f"Admin successfully edited contest3 description. New status: {updated_contest.status}.")

@pytest.mark.run(after='test_03_06_admin_edits_contest3_succeeds')
async def test_03_07_user2_assign_judge1_to_contest3_fails(client: AsyncClient): # Changed
    """User 2 attempts to assign judge1 (User 1's AI agent) to contest3 (User 2's contest). Fails."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "judge1_id" in test_data, "Judge 1 ID not found."
    
    assign_payload = {"agent_judge_id": test_data["judge1_id"]}
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

    assign_payload = {"agent_judge_id": test_data["judge1_id"]}
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

    assign_payload = {"user_judge_id": test_data["user1_id"]}
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

    payload_ai = {"agent_judge_id": test_data["judge1_id"]}
    response_ai = await client.post( # Changed
        f"/contests/{test_data['contest1_id']}/judges", # Path was already correct
        json=payload_ai,
        headers=test_data["user1_headers"]
    )
    assert response_ai.status_code in [200, 201], f"User 1 assigning own judge1 to contest1 failed: {response_ai.text}"
    print(f"User 1 assigned own AI judge1 (ID: {test_data['judge1_id']}) to contest1 successfully.")

    payload_human = {"user_judge_id": test_data["user2_id"]}
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

    assign_payload = {"user_judge_id": test_data["user2_id"]}
    response = await client.post( # Changed
        f"/contests/{test_data['contest3_id']}/judges", # Path was already correct
        json=assign_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 assigning self as judge to contest3 failed: {response.text}"
    print(f"User 2 assigned self (ID: {test_data['user2_id']}) as human judge to contest3 successfully.")

@pytest.mark.run(after='test_03_11_user2_assigns_self_as_judge_to_contest3_succeeds')
async def test_03_12_visitor_lists_contests(client: AsyncClient): # Changed
    """Visitor lists contests -> Should see publicly listed contests only."""
    response = await client.get("/contests/") # Changed
    # Expect 200 OK now
    assert response.status_code == 200, f"Visitor listing contests failed: {response.text}"
    contests = [ContestResponse(**c) for c in response.json()]
    
    # Visitor should see publicly listed contests only
    contest_ids_visible = {c.id for c in contests}
    assert test_data["contest1_id"] in contest_ids_visible, "Contest 1 not visible to visitor."
    assert test_data["contest2_id"] in contest_ids_visible, "Contest 2 (password-protected but publicly listed) not visible to visitor in list."
    assert test_data["contest3_id"] in contest_ids_visible, "Contest 3 not visible to visitor."
    # contest4 should not be visible as it's not publicly listed
    if "contest4_id" in test_data:
        assert test_data["contest4_id"] not in contest_ids_visible, "Contest 4 (non-publicly listed) should not be visible to visitor."
    print("Visitor listed contests successfully, saw publicly listed contests only.")

@pytest.mark.run(after='test_03_12_visitor_lists_contests')
async def test_03_13_user1_lists_contests(client: AsyncClient): # Changed
    """User 1 lists contests -> Should see publicly listed contests and own non-publicly listed contests."""
    assert "user1_headers" in test_data, "User 1 token not found."
    response = await client.get("/contests/", headers=test_data["user1_headers"]) # Changed
    assert response.status_code == 200, f"User 1 listing contests failed: {response.text}"
    contests = [ContestResponse(**c) for c in response.json()]

    contest_ids_visible = {c.id for c in contests}
    # User 1 should see publicly listed contests and their own non-publicly listed contests
    assert test_data["contest1_id"] in contest_ids_visible, "Contest 1 not visible to User 1."
    assert test_data["contest2_id"] in contest_ids_visible, "Contest 2 (password-protected but publicly listed) not visible to User 1 in list."
    assert test_data["contest3_id"] in contest_ids_visible, "Contest 3 not visible to User 1."
    # contest4 should be visible to user1 as they are the creator
    if "contest4_id" in test_data:
        assert test_data["contest4_id"] in contest_ids_visible, "Contest 4 (non-publicly listed, owned by User 1) should be visible to User 1."
    print("User 1 listed contests successfully, saw publicly listed contests and own non-publicly listed contests.")

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

@pytest.mark.run(after='test_03_18_admin_view_contest2_details_no_password_succeeds')
async def test_03_19_user1_creates_non_publicly_listed_contest4_for_member_testing(client: AsyncClient):
    """User 1 creates a non-publicly listed contest (contest4) for member testing."""
    assert "user1_headers" in test_data, "User 1 token not found."

    contest_in = ContestCreate(
        title="User1's Non-Publicly Listed Contest",
        description="A private contest for members only!",
        password_protected=False,
        publicly_listed=False,  # Non-publicly listed
        judge_restrictions=False,
        author_restrictions=False
    )
    response = await client.post(
        "/contests/",
        json=contest_in.model_dump(),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 201, f"User 1 creating contest4 failed: {response.text}"
    contest4_data = ContestResponse(**response.json())
    assert contest4_data.title == contest_in.title
    assert not contest4_data.password_protected
    assert not contest4_data.publicly_listed
    assert contest4_data.creator.id == test_data["user1_id"]
    test_data["contest4_id"] = contest4_data.id
    print(f"User 1 created non-publicly listed contest4 (ID: {test_data['contest4_id']}) successfully.")

@pytest.mark.run(after='test_03_19_user1_creates_non_publicly_listed_contest4_for_member_testing')
async def test_03_20_user2_cannot_access_contest4_not_publicly_listed(client: AsyncClient):
    """User 2 cannot access contest4 as it is not publicly listed."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest4_id" in test_data, "Contest 4 ID not found."

    response = await client.get(
        f"/contests/{test_data['contest4_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 accessing non-publicly listed contest4 should fail (403), got {response.status_code}: {response.text}"
    print("User 2 failed to access contest4 (not publicly listed) as expected.")

@pytest.mark.run(after='test_03_20_user2_cannot_access_contest4_not_publicly_listed')
async def test_03_21_user1_adds_user2_as_member_to_contest4(client: AsyncClient):
    """User 1 adds User 2 as member to contest4."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    assert "contest4_id" in test_data, "Contest 4 ID not found."

    member_data = {"user_id": test_data["user2_id"]}
    response = await client.post(
        f"/contests/{test_data['contest4_id']}/members",
        json=member_data,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 adding User 2 as member to contest4 failed: {response.text}"
    print(f"User 1 added User 2 (ID: {test_data['user2_id']}) as member to contest4 successfully.")

@pytest.mark.run(after='test_03_21_user1_adds_user2_as_member_to_contest4')
async def test_03_22_user2_can_access_contest4_as_member(client: AsyncClient):
    """User 2 can access contest4 as a member."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest4_id" in test_data, "Contest 4 ID not found."

    response = await client.get(
        f"/contests/{test_data['contest4_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 accessing contest4 as member failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.id == test_data["contest4_id"]
    print("User 2 accessed contest4 as member successfully.")

@pytest.mark.run(after='test_03_22_user2_can_access_contest4_as_member')
async def test_03_23_visitor_attempts_to_list_and_access_contest4_fails(client: AsyncClient):
    """Visitor user attempts to list and access contest4 -> Fails."""
    # Test listing contests as visitor - contest4 should not appear
    response = await client.get("/contests/")
    assert response.status_code == 200, f"Visitor listing contests failed: {response.text}"
    contests = [ContestResponse(**c) for c in response.json()]
    
    contest_ids_visible = {c.id for c in contests}
    assert test_data["contest4_id"] not in contest_ids_visible, "Contest 4 (non-publicly listed) should not be visible to visitor in list."
    print("Visitor correctly cannot see contest4 in contest list.")
    
    # Test direct access to contest4 as visitor - should get 401 (Authentication required)
    response = await client.get(f"/contests/{test_data['contest4_id']}")
    assert response.status_code == 401, f"Visitor accessing contest4 should fail (401), got {response.status_code}: {response.text}"
    print("Visitor failed to access contest4 directly as expected (401 - Authentication required).")

@pytest.mark.run(after='test_03_23_visitor_attempts_to_list_and_access_contest4_fails')
async def test_03_24_user1_removes_user2_from_contest4_members(client: AsyncClient):
    """User1 removes User 2 from contest4 members."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    assert "contest4_id" in test_data, "Contest 4 ID not found."

    response = await client.delete(
        f"/contests/{test_data['contest4_id']}/members/{test_data['user2_id']}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 204, f"User 1 removing User 2 from contest4 members failed: {response.text}"
    print(f"User 1 removed User 2 (ID: {test_data['user2_id']}) from contest4 members successfully.")

@pytest.mark.run(after='test_03_24_user1_removes_user2_from_contest4_members')
async def test_03_25_user2_can_no_longer_access_contest4(client: AsyncClient):
    """User 2 can no longer access contest4."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest4_id" in test_data, "Contest 4 ID not found."

    response = await client.get(
        f"/contests/{test_data['contest4_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 accessing contest4 after removal should fail (403), got {response.status_code}: {response.text}"
    print("User 2 can no longer access contest4 after being removed from members, as expected.")


# --- End of Test Section 3 ---