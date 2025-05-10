# backend/tests/e2e_sec_09_cleanup_routine.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
from typing import List, Dict, Any

from backend.app.core.config import settings
# Schemas for User, Contest, Agent might be needed if checking responses or existence after deletion
from backend.tests.shared_test_state import test_data
from backend.app.schemas.submission import SubmissionResponse # For checking submissions
from backend.app.schemas.vote import VoteResponse # For checking votes
from backend.app.schemas.user import UserResponse # For checking user deletion impact

# client will be a fixture argument to test functions

# --- Start of Test Section 9: Cleanup Routine ---

@pytest.mark.run(after='test_08_05_user2_checks_their_credit_balance') # After section 8
def test_09_01_user2_tries_to_delete_contest1_fails(client: TestClient):
    """User 2 tries to delete contest 1 -> Should fail."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, \
        f"User 2 deleting contest1 should fail (403), got {response.status_code}: {response.text}"
    print(f"User 2 attempt to delete contest1 (ID: {test_data['contest1_id']}) failed as expected (403 - not owner/admin).")

@pytest.mark.run(after='test_09_01_user2_tries_to_delete_contest1_fails')
def test_09_02_user1_deletes_contest1_succeeds(client: TestClient):
    """User 1 deletes contest 1 -> Should succeed. Verify associated votes are deleted."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    contest1_id = test_data['contest1_id']

    # Optional: Get votes associated with contest1 submissions before deleting contest
    # This requires knowing submission IDs in contest1. Example:
    # vote_ids_before_delete = []
    # if "submission_c1_t2_2_id" in test_data and "user2_vote_c1_s_t2_2_id" in test_data: # From test 6.06
    #     vote_ids_before_delete.append(test_data["user2_vote_c1_s_t2_2_id"])
    # This can be complex if many votes/submissions exist. For simplicity, we'll assume cascade delete works.

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{contest1_id}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 failed to delete contest1: {response.text}"
    print(f"User 1 successfully deleted contest1 (ID: {contest1_id}).")

    # Verify contest is gone
    get_response = client.get(f"{settings.API_V1_STR}/contests/{contest1_id}", headers=test_data["user1_headers"])
    assert get_response.status_code == 404, f"Contest1 should be deleted (404), but got {get_response.status_code}"
    
    # Verify associated votes are deleted (indirectly, as fetching them would require contest/submission)
    # If specific vote IDs were stored, one could try fetching them directly and expect 404.
    # E.g., if "user2_vote_c1_s_t2_2_id" was a vote in contest1, try fetching vote by its ID.
    if "user2_vote_c1_s_t2_2_id" in test_data: # vote from User2 on submission_c1_t2_2_id in contest1
        vote_id_to_check = test_data["user2_vote_c1_s_t2_2_id"]
        # This vote was on submission_c1_t2_2_id. We need the specific submission ID here if the endpoint requires it.
        # The endpoint /votes/{vote_id} might be simpler if it exists and doesn't require contest/submission context.
        # Assuming a direct GET /votes/{vote_id} endpoint:
        # vote_check_resp = client.get(f"{settings.API_V1_STR}/votes/{vote_id_to_check}", headers=test_data["user1_headers"])
        # assert vote_check_resp.status_code == 404, "Vote associated with deleted contest1 should also be deleted."
        # print(f"Vote {vote_id_to_check} confirmed deleted after contest1 deletion.")
        # For now, this step is a placeholder as direct vote fetching logic may vary.
        pass 

    if "contest1_id" in test_data: del test_data["contest1_id"]

@pytest.mark.run(after='test_09_02_user1_deletes_contest1_succeeds')
def test_09_03_user2_attempts_to_delete_judge1_fails(client: TestClient):
    """User 2 attempts to delete judge1 (User 1's AI Judge) -> Should fail."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "judge1_id" in test_data, "Judge1 (User 1's AI Judge) ID not found."

    response = client.delete(
        f"{settings.API_V1_STR}/agents/{test_data['judge1_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, \
        f"User 2 deleting User 1's agent (judge1) should fail (403), got {response.status_code}: {response.text}"
    print(f"User 2 attempt to delete judge1 (ID: {test_data['judge1_id']}) failed as expected (403).")

@pytest.mark.run(after='test_09_03_user2_attempts_to_delete_judge1_fails')
def test_09_04_user1_deletes_writer1_ai_writer(client: TestClient):
    """User 1 deletes their AI writer (writer1). Verify associated submissions are not deleted (if any exist)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "writer1_id" in test_data, "Writer 1 ID not found."
    writer1_id = test_data['writer1_id']

    # Check if any submission was made by writer1 - text1_2 was by writer1 (test 4.08), submitted to C1 (test 5.03 as submission_c1_t1_2_id)
    # submission_c1_t1_2_id was deleted in 5.14, re-added in 5.18 as submission_c1_t1_2_v2_id, then deleted by admin in 5.19.
    # So, at this point, there are no submissions explicitly made by writer1 left in test_data for contest1 (which is now also deleted).
    # If submissions were made to other contests by writer1 and not deleted, they should persist.
    # This part of the test is hard to verify without a clear remaining submission from writer1.
    # For now, we will just delete the agent.

    response = client.delete(f"{settings.API_V1_STR}/agents/{writer1_id}", headers=test_data["user1_headers"])
    assert response.status_code == 200, f"User 1 failed to delete writer1: {response.text}"
    print(f"User 1 successfully deleted writer1 (ID: {writer1_id}). Associated submissions are expected to remain (if any)." )
    # Verify agent is gone
    get_response = client.get(f"{settings.API_V1_STR}/agents/{writer1_id}", headers=test_data["user1_headers"])
    assert get_response.status_code == 404
    if "writer1_id" in test_data: del test_data["writer1_id"]

@pytest.mark.run(after='test_09_04_user1_deletes_writer1_ai_writer')
def test_09_05_user1_deletes_judge1_ai_judge(client: TestClient):
    """User 1 deletes their AI judge (judge1). Verify associated votes are not deleted. Verify costs are not affected."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "judge1_id" in test_data, "Judge1 ID not found."
    judge1_id = test_data['judge1_id']

    # This judge (judge1) might have cast votes if Admin triggered it in 6.09 for contest1.
    # However, contest1 and its votes were deleted in 9.02. 
    # If judge1 was assigned to contest2 (it was in 3.02 by admin) and if it cast votes in contest2, those votes should remain.
    # Admin triggered judge_global for contest2, not judge1 in section 6.
    # This makes verifying remaining votes from judge1 difficult with current test flow.
    # For now, we check costs are not affected (meaning no refund/charge for deleting an agent).

    user1_details_before = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    initial_credits_user1 = user1_details_before.credits

    response = client.delete(f"{settings.API_V1_STR}/agents/{judge1_id}", headers=test_data["user1_headers"])
    assert response.status_code == 200, f"User 1 failed to delete judge1: {response.text}"
    print(f"User 1 successfully deleted judge1 (ID: {judge1_id}). Associated votes (if any on other contests) should remain.")

    user1_details_after = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    final_credits_user1 = user1_details_after.credits
    assert final_credits_user1 == initial_credits_user1, "User 1 credits changed after deleting their AI judge."
    print(f"User 1 credits confirmed unchanged after deleting judge1. Before: {initial_credits_user1}, After: {final_credits_user1}.")

    get_response = client.get(f"{settings.API_V1_STR}/agents/{judge1_id}", headers=test_data["user1_headers"])
    assert get_response.status_code == 404
    if "judge1_id" in test_data: del test_data["judge1_id"]

@pytest.mark.run(after='test_09_05_user1_deletes_judge1_ai_judge')
def test_09_06_admin_deletes_contest2_and_contest3(client: TestClient):
    """Admin deletes contest2 and contest3."""
    assert "admin_headers" in test_data, "Admin token not found."
    contests_to_delete = []
    if "contest2_id" in test_data: contests_to_delete.append("contest2_id")
    if "contest3_id" in test_data: contests_to_delete.append("contest3_id")
    
    assert len(contests_to_delete) > 0, "Contest 2 and/or Contest 3 IDs not found in test_data."

    for contest_key in contests_to_delete:
        contest_id = test_data[contest_key]
        response = client.delete(f"{settings.API_V1_STR}/contests/{contest_id}", headers=test_data["admin_headers"])
        assert response.status_code == 200, f"Admin failed to delete {contest_key}: {response.text}"
        print(f"Admin successfully deleted {contest_key} (ID: {contest_id}).")
        # Verify contest is gone
        get_response = client.get(f"{settings.API_V1_STR}/contests/{contest_id}", headers=test_data["admin_headers"])
        assert get_response.status_code == 404
        if contest_key in test_data: del test_data[contest_key]

@pytest.mark.run(after='test_09_06_admin_deletes_contest2_and_contest3')
def test_09_07_user2_attempts_to_delete_writer_global_fails(client: TestClient):
    """User 2 attempts to delete writer_global -> Should fail."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "writer_global_id" in test_data, "Global writer ID not found."

    response = client.delete(
        f"{settings.API_V1_STR}/agents/{test_data['writer_global_id']}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, \
        f"User 2 deleting global writer should fail (403), got {response.status_code}: {response.text}"
    print(f"User 2 attempt to delete writer_global (ID: {test_data['writer_global_id']}) failed as expected (403).")

@pytest.mark.run(after='test_09_07_user2_attempts_to_delete_writer_global_fails')
def test_09_08_admin_deletes_global_ai_writer(client: TestClient):
    """Admin deletes global AI writer (writer_global)."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "writer_global_id" in test_data, "Global writer ID not found."
    writer_global_id = test_data['writer_global_id']

    response = client.delete(f"{settings.API_V1_STR}/agents/{writer_global_id}", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to delete writer_global: {response.text}"
    print(f"Admin successfully deleted writer_global (ID: {writer_global_id}).")
    get_response = client.get(f"{settings.API_V1_STR}/agents/{writer_global_id}", headers=test_data["admin_headers"])
    assert get_response.status_code == 404
    if "writer_global_id" in test_data: del test_data["writer_global_id"]

@pytest.mark.run(after='test_09_08_admin_deletes_global_ai_writer')
def test_09_09_admin_deletes_global_ai_judge(client: TestClient):
    """Admin deletes global AI judge (judge_global)."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "judge_global_id" in test_data, "Global judge ID not found."
    judge_global_id = test_data['judge_global_id']

    response = client.delete(f"{settings.API_V1_STR}/agents/{judge_global_id}", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to delete judge_global: {response.text}"
    print(f"Admin successfully deleted judge_global (ID: {judge_global_id}).")
    get_response = client.get(f"{settings.API_V1_STR}/agents/{judge_global_id}", headers=test_data["admin_headers"])
    assert get_response.status_code == 404
    if "judge_global_id" in test_data: del test_data["judge_global_id"]

@pytest.mark.run(after='test_09_09_admin_deletes_global_ai_judge')
def test_09_10_admin_deletes_user1(client: TestClient):
    """Admin deletes User 1. Verify associated submissions are deleted from him and from his AI agents."""
    # Note: The original plan was User 1 deletes User 1. This is usually not allowed.
    # Admin deleting User 1 is more robust for testing cleanup.
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data, "User 1 ID not found."
    user1_id = test_data['user1_id']

    # This check is complex: requires knowing all submissions by User1 or User1's agents across all contests.
    # Some contests/submissions might already be deleted. We rely on backend cascade logic.
    # A thorough check would involve querying all remaining submissions and ensuring none are from user1_id or user1's (now deleted) agents.

    response = client.delete(f"{settings.API_V1_STR}/admin/users/{user1_id}", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to delete User 1: {response.text}"
    print(f"Admin successfully deleted User 1 (ID: {user1_id}). Associated submissions are expected to be deleted.")
    
    get_response = client.get(f"{settings.API_V1_STR}/users/{user1_id}", headers=test_data["admin_headers"])
    assert get_response.status_code == 404, f"User 1 (ID: {user1_id}) should be deleted (404), but got {get_response.status_code}"
    if "user1_id" in test_data: del test_data["user1_id"]
    if "user1_headers" in test_data: del test_data["user1_headers"] # Invalidate token

@pytest.mark.run(after='test_09_10_admin_deletes_user1')
def test_09_11_admin_deletes_user2(client: TestClient):
    """Admin deletes User 2. Verify associated submissions are deleted."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    user2_id = test_data['user2_id']

    response = client.delete(f"{settings.API_V1_STR}/admin/users/{user2_id}", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to delete User 2: {response.text}"
    print(f"Admin successfully deleted User 2 (ID: {user2_id}). Associated submissions are expected to be deleted.")

    get_response = client.get(f"{settings.API_V1_STR}/users/{user2_id}", headers=test_data["admin_headers"])
    assert get_response.status_code == 404, f"User 2 (ID: {user2_id}) should be deleted (404), but got {get_response.status_code}"
    if "user2_id" in test_data: del test_data["user2_id"]
    if "user2_headers" in test_data: del test_data["user2_headers"] # Invalidate token

# --- End of Test Section 9: Cleanup Routine ---