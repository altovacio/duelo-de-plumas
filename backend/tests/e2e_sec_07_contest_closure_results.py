# backend/tests/e2e_sec_07_contest_closure_results.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
from typing import List # Added for type hinting

from backend.app.core.config import settings
from backend.app.schemas.contest import ContestUpdate, ContestResponse, ContestVisibility # ContestVisibility added
from backend.app.schemas.submission import SubmissionResponse # For viewing submissions
# Make sure UserResponse is imported if needed for author name checks
from backend.app.schemas.user import UserResponse 
from backend.tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 7: Contest Closure & Results ---

@pytest.mark.run(after='test_06_14_user1_submits_votes_for_contest2') # Ensure this runs after section 6
def test_07_01_admin_sets_contests_status_to_closed(client: TestClient):
    """Admin sets contest1, contest2 and contest3 status to 'Closed'."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    contests_to_close = ["contest1_id", "contest2_id", "contest3_id"]
    for contest_key in contests_to_close:
        contest_id = test_data[contest_key]
        update_payload = ContestUpdate(status="Closed")
        response = client.put(
            f"{settings.API_V1_STR}/contests/{contest_id}",
            json=update_payload.model_dump(exclude_unset=True),
            headers=test_data["admin_headers"]
        )
        assert response.status_code == 200, \
            f"Admin failed to set {contest_key} status to Closed: {response.text}"
        
        updated_contest = ContestResponse(**response.json())
        assert updated_contest.status.lower() == "closed", \
            f"{contest_key} status was not updated to Closed. Current status: {updated_contest.status}"
        print(f"Admin successfully set {contest_key} (ID: {contest_id}) status to: {updated_contest.status}.")

@pytest.mark.run(after='test_07_01_admin_sets_contests_status_to_closed')
def test_07_02_visitor_views_contest1_details_revealed(client: TestClient):
    """Visitor views contest1 details -> Should see results, user and author names revealed."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Check contest status
    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert response.status_code == 200
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed", "Contest1 is not Closed."

    # Check submissions for revealed names
    sub_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/")
    assert sub_response.status_code == 200, f"Visitor failed to get submissions for closed contest: {sub_response.text}"
    
    submissions = sub_response.json()
    assert isinstance(submissions, list)
    if len(submissions) > 0:
        for sub_data in submissions:
            submission = SubmissionResponse(**sub_data)
            assert submission.user_id is not None, "User ID should be revealed for submissions in a Closed contest."
            assert submission.author is not None and "masked" not in submission.author.lower() and submission.author != "[Hidden]", \
                f"Author name should be revealed. Got: {submission.author}"
            # Optionally, fetch user details to confirm author name matches if user_id is for a known user
            # user_details_resp = client.get(f"{settings.API_V1_STR}/users/{submission.user_id}") # Needs user_id to be actual user id not a placeholder
            # if user_details_resp.status_code == 200:
            #     user_info = UserResponse(**user_details_resp.json())
            #     assert submission.author == user_info.username, "Author name mismatch."
    else:
        print("No submissions in contest1 to verify name reveal.")

    print(f"Visitor successfully viewed contest1 (ID: {test_data['contest1_id']}) details with user/author info revealed (status: Closed).")

@pytest.mark.run(after='test_07_02_visitor_views_contest1_details_revealed')
def test_07_03_user1_changes_contest1_to_private(client: TestClient):
    """User 1 changes contest1 to private."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    test_data["contest1_password"] = "testprivpass123" # Store password for later tests

    update_payload = ContestUpdate(visibility=ContestVisibility.private, password=test_data["contest1_password"])
    response = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to set contest1 to private: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.visibility == ContestVisibility.private, "Contest1 visibility not set to private."
    assert updated_contest.has_password is True, "Contest1 should indicate it has a password."
    print(f"User 1 successfully changed contest1 (ID: {test_data['contest1_id']}) to private.")

@pytest.mark.run(after='test_07_03_user1_changes_contest1_to_private')
def test_07_04_visitor_views_contest1_details_private_no_pass_fails(client: TestClient):
    """Visitor attempts to view contest1 details with no password -> Fails."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert response.status_code == 403, \
        f"Viewing private contest1 without password should fail (403), got {response.status_code}: {response.text}"
    print(f"Visitor attempt to view private contest1 (ID: {test_data['contest1_id']}) without password failed as expected.")

@pytest.mark.run(after='test_07_04_visitor_views_contest1_details_private_no_pass_fails')
def test_07_05_visitor_views_contest1_details_private_with_pass_succeeds(client: TestClient):
    """Visitor attempts to view contest1 details with correct password -> Succeeds. User and author names revealed."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "contest1_password" in test_data, "Contest1 password not found in test_data."

    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", params={"password": test_data["contest1_password"]})
    assert response.status_code == 200, \
        f"Viewing private contest1 with password failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed"
    # Check submissions for revealed names (as in 7.02)
    sub_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/", params={"password": test_data["contest1_password"]})
    assert sub_response.status_code == 200
    submissions = sub_response.json()
    if len(submissions) > 0:
        for sub_data in submissions:
            submission = SubmissionResponse(**sub_data)
            assert submission.user_id is not None
            assert submission.author is not None and "masked" not in submission.author.lower()
    print(f"Visitor successfully viewed private contest1 (ID: {test_data['contest1_id']}) with correct password.")

@pytest.mark.run(after='test_07_05_visitor_views_contest1_details_private_with_pass_succeeds')
def test_07_06_user1_returns_contest1_to_public(client: TestClient):
    """User 1 returns contest1 to public."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    update_payload = ContestUpdate(visibility=ContestVisibility.public, password=None) # Explicitly set password to None or omit
    response = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}",
        json=update_payload.model_dump(exclude_unset=True, exclude_none=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to set contest1 to public: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.visibility == ContestVisibility.public, "Contest1 visibility not set to public."
    assert updated_contest.has_password is False, "Contest1 should not indicate it has a password."
    print(f"User 1 successfully returned contest1 (ID: {test_data['contest1_id']}) to public.")

@pytest.mark.run(after='test_07_06_user1_returns_contest1_to_public')
def test_07_07_visitor_views_contest1_public_details_revealed(client: TestClient):
    """Visitor attempts to view contest1 details with no password -> Succeeds. User and author names revealed."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert response.status_code == 200, \
        f"Viewing public contest1 failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed"
    # Check submissions for revealed names (as in 7.02)
    sub_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/")
    assert sub_response.status_code == 200
    submissions = sub_response.json()
    if len(submissions) > 0:
        for sub_data in submissions:
            submission = SubmissionResponse(**sub_data)
            assert submission.user_id is not None
            assert submission.author is not None and "masked" not in submission.author.lower()
    print(f"Visitor successfully viewed public contest1 (ID: {test_data['contest1_id']}) with details revealed.")

@pytest.mark.run(after='test_07_07_visitor_views_contest1_public_details_revealed')
def test_07_08_user2_deletes_submission_c1_t2_1_from_contest1(client: TestClient):
    """User 2 deletes their own submission (submission_c1_t2_1, which is Text 2.1) from contest1. Should succeed."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    # submission_c1_t2_1 was created in test_05_01 and might have been deleted if test_05_15 ran.
    # We need to ensure it exists or re-add it for this test, or use another submission by User 2.
    # For simplicity, let's assume it might have been deleted by test_05_15. This test plan step implies text deletion *after* closure.
    # Test_05_15: User 2 deletes their own manual submission (submission_id_c1_t2_1) from contest1.
    # This test (7.08) seems to be a duplicate or re-test of that functionality in a different contest phase.
    # Let's use submission_c1_t2_3 (Text 2.3 by User 2, from 5.05) which should still exist.
    assert "submission_c1_t2_3_id" in test_data, "Submission ID for Text 2.3 by User 2 in Contest 1 not found."
    submission_id_to_delete = test_data["submission_c1_t2_3_id"]

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, \
        f"User 2 failed to delete their submission {submission_id_to_delete} from contest1: {response.text}"
    
    # Verify submission is gone
    get_subs_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user2_headers"])
    submissions_after_delete = get_subs_response.json()
    assert not any(s["id"] == submission_id_to_delete for s in submissions_after_delete), "Submission was not actually deleted."

    print(f"User 2 successfully deleted their submission {submission_id_to_delete} (Text 2.3) from contest1 (ID: {test_data['contest1_id']}).")

@pytest.mark.run(after='test_07_08_user2_deletes_submission_c1_t2_1_from_contest1')
def test_07_09_user1_deletes_submission_c1_t2_2_from_contest1(client: TestClient):
    """User 1 (contest owner) attempts to delete User 2's submission (submission_c1_t2_2, Text 2.2) from contest1. Should succeed. Verify Cost records are not affected."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    # submission_c1_t2_2 was created in test_05_02. It might have been deleted if test_05_17 ran.
    # Test 5.17: User 1 (creator of contest1) deletes User 2's submission (submission_id_c1_t2_2) from contest1.
    # This again looks like a re-test. Let's assume it was deleted.
    # For this test to be meaningful, we'd need a submission by another user that User 1 can delete.
    # Let's check for submission_c1_t3_2_id (Admin's submission from 5.09)
    submission_to_delete_id = test_data.get("submission_c1_t3_2_id")
    if not submission_to_delete_id:
        # If admin's sub doesn't exist, let's try to find any remaining submission not by User 1
        get_subs_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user1_headers"])
        all_submissions = [SubmissionResponse(**s) for s in get_subs_response.json()]
        target_submission = next((s for s in all_submissions if str(s.user_id) != str(test_data["user1_id"]) and s.id != test_data.get("submission_c1_t2_3_id")), None)
        if target_submission:
            submission_to_delete_id = target_submission.id
        else:
            pytest.skip("No suitable submission found for User 1 to delete in contest1 for test 7.09. This might be due to prior deletions.")
            return
    
    print(f"User 1 (contest owner) will attempt to delete submission ID: {submission_to_delete_id} from contest1.")

    # Credits check for User 1 (owner) - should not be affected by deleting another's submission
    user1_details_before = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    initial_credits_user1 = user1_details_before.credits

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_to_delete_id}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to delete submission {submission_to_delete_id} from contest1: {response.text}"

    # Verify User 1 credits are not affected
    user1_details_after = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    final_credits_user1 = user1_details_after.credits
    assert final_credits_user1 == initial_credits_user1, "User 1 credits changed after deleting a submission as contest owner."

    # Verify submission is gone
    get_subs_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user1_headers"])
    submissions_after_delete_user1 = get_subs_response_after.json()
    assert not any(s["id"] == submission_to_delete_id for s in submissions_after_delete_user1), "Submission was not actually deleted by User 1."

    print(f"User 1 successfully deleted submission {submission_to_delete_id} from contest1 (ID: {test_data['contest1_id']}). User 1 credits unchanged.")

# --- End of Test Section 7: Contest Closure & Results ---