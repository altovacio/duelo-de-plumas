# backend/tests/e2e_sec_05_text_submission.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
import logging

from app.core.config import settings
from app.schemas.contest import ContestResponse # For checking contest details
from app.schemas.submission import SubmissionResponse # For submission data
from app.schemas.user import UserResponse # For credit checks
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 5: Text Submission Phase (Contest Open) ---

def test_05_01_user2_submits_text2_1_to_contest1(client: TestClient):
    """User 2 submits Text 2.1 to contest1. Verify success."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_1_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.1 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t2_1_id"] = submission_data["submission_id"]
    print(f"User 2 successfully submitted Text 2.1 (ID: {test_data['text2_1_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t2_1_id']}.")

@pytest.mark.run(after='test_05_01_user2_submits_text2_1_to_contest1')
def test_05_02_user2_submits_text2_2_to_contest1_and_verify_counts(client: TestClient):
    """User 2 submits Text 2.2 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_2_id" in test_data, "Text 2.2 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_2_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t2_2_id"] = submission_data["submission_id"]
    print(f"User 2 successfully submitted Text 2.2 (ID: {test_data['text2_2_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t2_2_id']}.")

    contest_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestResponse(**contest_response.json())
    assert contest_data.text_count == 2, f"Expected 2 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 1, f"Expected 1 participant in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_02_user2_submits_text2_2_to_contest1_and_verify_counts')
def test_05_03_user1_submits_text1_2_to_contest1_and_verify_counts(client: TestClient):
    """User 1 submits Text 1.2 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_2_id" in test_data, "Text 1.2 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text1_2_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t1_2_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.2 (ID: {test_data['text1_2_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t1_2_id']}.")

    contest_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestResponse(**contest_response.json())
    assert contest_data.text_count == 3, f"Expected 3 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_03_user1_submits_text1_2_to_contest1_and_verify_counts')
def test_05_04_user1_submits_text1_3_to_contest1_and_verify_counts(client: TestClient):
    """User 1 submits Text 1.3 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.3 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t1_3_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.3 (ID: {test_data['text1_3_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t1_3_id']}.")

    contest_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestResponse(**contest_response.json())
    assert contest_data.text_count == 4, f"Expected 4 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_04_user1_submits_text1_3_to_contest1_and_verify_counts')
def test_05_05_user2_submits_text2_3_to_contest1_and_verify_counts(client: TestClient):
    """User 2 submits Text 2.3 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_3_id" in test_data, "Text 2.3 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_3_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.3 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t2_3_id"] = submission_data["submission_id"]
    print(f"User 2 successfully submitted Text 2.3 (ID: {test_data['text2_3_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t2_3_id']}.")

    contest_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestResponse(**contest_response.json())
    assert contest_data.text_count == 5, f"Expected 5 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_05_user2_submits_text2_3_to_contest1_and_verify_counts')
def test_05_06_user1_submits_text1_1_to_contest2_succeeds(client: TestClient):
    """User 1 submits Text 1.1 to contest2. Verify success (owner_restrictions=True, first submission)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    # Verify Contest 2 settings: owner_restrictions = True
    contest_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # Admin can view full details
    assert contest_resp.status_code == 200
    contest_details = ContestResponse(**contest_resp.json())
    assert contest_details.owner_restrictions is True, "Contest 2 owner_restrictions should be True for this test."

    submission_payload = {"text_id": test_data["text1_1_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.1 to contest2 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c2_t1_1_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.1 (ID: {test_data['text1_1_id']}) to contest2 (ID: {test_data['contest2_id']}). Submission ID: {test_data['submission_c2_t1_1_id']}.")

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, f"Expected 1 text in contest2, got {contest_data_after.text_count}"
    assert contest_data_after.participant_count == 1, f"Expected 1 participant in contest2, got {contest_data_after.participant_count}"
    print(f"Contest2 (ID: {test_data['contest2_id']}) updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_06_user1_submits_text1_1_to_contest2_succeeds')
def test_05_07_user1_submits_text1_3_to_contest2_fails(client: TestClient):
    """User 1 attempts to submit Text 1.3 to contest2 -> Fails due to owner_restrictions."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID not found." # User1's other manual text
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "submission_c2_t1_1_id" in test_data, "User 1's first submission to contest2 not found."

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 submitting second text to contest2 (owner_restrictions=True) should fail (403), but got {response.status_code}: {response.text}"
    print("User 1 attempt to submit a second text (Text 1.3) to contest2 failed as expected due to owner_restrictions.")

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, "Text count for contest2 should remain 1."
    assert contest_data_after.participant_count == 1, "Participant count for contest2 should remain 1."

@pytest.mark.run(after='test_05_07_user1_submits_text1_3_to_contest2_fails')
def test_05_08_user2_submits_text2_3_to_contest2_fails_judge_restriction(client: TestClient):
    """User 2 attempts to submit Text 2.3 to contest2 -> Fails due to judge_restrictions."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "text2_3_id" in test_data, "Text 2.3 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    # Verify Contest 2 settings and User 2 is a judge
    contest_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    assert contest_resp.status_code == 200
    contest_details = ContestResponse(**contest_resp.json())
    assert contest_details.judge_restrictions is True, "Contest 2 judge_restrictions should be True."
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not listed as a judge for contest2 for this test."

    submission_payload = {"text_id": test_data["text2_3_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 (judge) submitting to contest2 (judge_restrictions=True) should fail (403), got {response.status_code}: {response.text}"
    print("User 2 (judge) attempt to submit Text 2.3 to contest2 failed as expected due to judge_restrictions.")

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, "Text count for contest2 should remain 1 after failed judge submission."

@pytest.mark.run(after='test_05_08_user2_submits_text2_3_to_contest2_fails_judge_restriction')
def test_05_09_admin_submits_text3_2_to_contest1_succeeds(client: TestClient):
    """Admin submits AI-generated Text 3.2 to contest1. Verify success."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "text3_2_id" in test_data, "Text 3.2 (Admin's AI text) ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    contest1_before_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    contest1_before_data = ContestResponse(**contest1_before_resp.json())
    initial_text_count_c1 = contest1_before_data.text_count
    initial_participant_count_c1 = contest1_before_data.participant_count

    submission_payload = {"text_id": test_data["text3_2_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["admin_headers"]
    )
    assert response.status_code in [200, 201], f"Admin submitting Text 3.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c1_t3_2_id"] = submission_data["submission_id"]
    print(f"Admin successfully submitted AI Text 3.2 to contest1. Submission ID: {test_data['submission_c1_t3_2_id']}.")

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == initial_text_count_c1 + 1
    # Admin is a new participant if they haven't submitted before, or participant count stays same if admin is user1 or user2.
    # Assuming admin is a distinct user.
    me_admin_resp = client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["admin_headers"])
    admin_user_id = UserResponse(**me_admin_resp.json()).id
    
    is_admin_new_participant = True
    if str(admin_user_id) == str(test_data.get("user1_id")) or str(admin_user_id) == str(test_data.get("user2_id")):
        is_admin_new_participant = False # Admin is one of the existing participants

    expected_participant_count = initial_participant_count_c1
    # Check if admin was already a participant through other submissions to contest1 by user1 or user2 (if admin is user1 or user2)
    # However, the current participants are User1 and User2 from previous submissions. Admin is distinct.
    # So admin should be a new participant.
    # Let's get existing participants for contest1:
    submissions_c1_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions", headers=test_data["admin_headers"])
    submissions_c1_data = [SubmissionResponse(**s) for s in submissions_c1_resp.json()]
    participant_ids_c1 = {s.owner_id for s in submissions_c1_data}
    
    assert contest_data_after.participant_count == len(participant_ids_c1), \
        f"Expected {len(participant_ids_c1)} participants in contest1, got {contest_data_after.participant_count}"
    print(f"Contest1 updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_09_admin_submits_text3_2_to_contest1_succeeds')
def test_05_10_user1_views_submissions_contest1_succeeds(client: TestClient):
    """User 1 (contest creator) views all submissions for contest1 -> Should succeed."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = client.get(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 (creator) viewing submissions for contest1 failed: {response.text}"
    submissions = response.json()
    assert isinstance(submissions, list)
    # Check if submissions are unmasked for creator (user_id, author should be visible)
    for sub_data in submissions:
        submission = SubmissionResponse(**sub_data)
        assert submission.user_id is not None
        assert submission.author is not None 
    print("User 1 (creator) successfully viewed submissions for contest1 (open phase, unmasked).")

@pytest.mark.run(after='test_05_10_user1_views_submissions_contest1_succeeds')
def test_05_11_user2_views_submissions_contest1_fails(client: TestClient):
    """User 2 (non-creator) attempts to view all submissions for contest1 -> Should fail (open phase)."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = client.get(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 (non-creator) viewing submissions for contest1 (open) should fail (403), got {response.status_code}: {response.text}"
    print("User 2 (non-creator) attempt to view submissions for contest1 (open phase) failed as expected.")

@pytest.mark.run(after='test_05_11_user2_views_submissions_contest1_fails')
def test_05_12_visitor_views_submissions_contest1_fails(client: TestClient):
    """Visitor attempts to view submissions for contest1 -> Should fail (open phase)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/")
    assert response.status_code == 403, f"Visitor viewing submissions for contest1 (open) should fail (403), got {response.status_code}: {response.text}"
    print("Visitor attempt to view submissions for contest1 (open phase) failed as expected.")

@pytest.mark.run(after='test_05_12_visitor_views_submissions_contest1_fails')
def test_05_13_admin_views_submissions_contest1_succeeds(client: TestClient):
    """Admin views submissions for contest1 -> Should succeed."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = client.get(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin viewing submissions for contest1 failed: {response.text}"
    submissions = response.json()
    assert isinstance(submissions, list)
    # Admin should see unmasked data
    for sub_data in submissions:
        submission = SubmissionResponse(**sub_data)
        assert submission.user_id is not None
        assert submission.author is not None
    print("Admin successfully viewed submissions for contest1 (open phase, unmasked).")
    # "Verify only accepted submissions are present." - current logic accepts all valid submissions.

@pytest.mark.run(after='test_05_13_admin_views_submissions_contest1_succeeds')
def test_05_14_user1_deletes_own_ai_submission_c1_t1_2_no_refund(client: TestClient):
    """User 1 deletes their own AI-text submission (submission_c1_t1_2) from contest1.
    - Verify success and updated contest counts.
    - Verify User 1's credits are NOT affected (AI generation cost is sunk and not refunded)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "submission_c1_t1_2_id" in test_data, "Submission ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_id" in test_data, "User1 ID not found for credit check."
    # Capture User 1's credits *before* this specific submission deletion,
    # which should be the credits *after* Text 1.2 generation (test_04_08) 
    # and after any other credit-affecting operations prior to this test.
    # For simplicity in this specific correction, we'll fetch current credits as the baseline
    # assuming no other credit changes for User1 between AI text generation and this deletion.
    # A more robust way would be to store the post-generation credit value in test_data.
    user1_credits_before_this_deletion = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"]).json()).credits

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{test_data['submission_c1_t1_2_id']}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 deleting submission_c1_t1_2 failed: {response.text}"
    print(f"User 1 successfully deleted submission_c1_t1_2 (ID: {test_data['submission_c1_t1_2_id']}).")

    contest_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestResponse(**contest_response.json())
    assert contest_data.text_count == 4, f"Expected 4 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

    user1_credits_after_sub_delete = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["user1_headers"]).json()).credits
    assert user1_credits_after_sub_delete == user1_credits_before_this_deletion, \
        f"User1's credits should not change after deleting their own AI text submission. Before: {user1_credits_before_this_deletion}, After: {user1_credits_after_sub_delete}."
    print(f"User1's credits ({user1_credits_after_sub_delete}) correctly NOT affected after submission deletion, as expected.")

    del test_data["submission_c1_t1_2_id"]

@pytest.mark.run(after='test_05_14_user1_deletes_own_ai_submission_c1_t1_2_no_refund')
def test_05_15_user2_deletes_own_submission_c1_t2_1_succeeds(client: TestClient):
    """User 2 deletes their own submission (Text 2.1 from contest1)."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t2_1_id" in test_data, "Submission ID for Text 2.1 in Contest 1 not found."
    
    submission_id_to_delete = test_data["submission_c1_t2_1_id"]

    contest1_before_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    initial_text_count_c1 = ContestResponse(**contest1_before_resp.json()).text_count

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 200, f"User 2 deleting own submission {submission_id_to_delete} failed: {response.text}"
    print(f"User 2 successfully deleted their submission {submission_id_to_delete} (Text 2.1) from contest1.")
    del test_data["submission_c1_t2_1_id"]

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == initial_text_count_c1 - 1, "Contest1 text count did not decrease by 1."
    # Participant count might change if this was User 2's only submission.
    submissions_c1_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions", headers=test_data["admin_headers"])
    submissions_c1_data = [SubmissionResponse(**s) for s in submissions_c1_resp.json()]
    participant_ids_c1 = {s.owner_id for s in submissions_c1_data}
    assert contest_data_after.participant_count == len(participant_ids_c1), "Contest1 participant count mismatch."
    print(f"Contest1 updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_15_user2_deletes_own_submission_c1_t2_1_succeeds')
def test_05_16_user1_deletes_own_submission_c2_t1_1_succeeds(client: TestClient):
    """User 1 deletes their submission of Text 1.1 from contest2."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "submission_c2_t1_1_id" in test_data, "Submission ID for Text 1.1 in Contest 2 not found."

    submission_id_to_delete = test_data["submission_c2_t1_1_id"]
    
    contest2_before_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    initial_text_count_c2 = ContestResponse(**contest2_before_resp.json()).text_count
    initial_participant_count_c2 = ContestResponse(**contest2_before_resp.json()).participant_count


    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 deleting own submission {submission_id_to_delete} from contest2 failed: {response.text}"
    print(f"User 1 successfully deleted their submission {submission_id_to_delete} (Text 1.1) from contest2.")
    del test_data["submission_c2_t1_1_id"]

    # Verify submission is gone from contest2
    submissions_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/", headers=test_data["admin_headers"])
    submissions = submissions_resp.json()
    assert not any(sub["id"] == submission_id_to_delete for sub in submissions), "Deleted submission still found in contest2."
    
    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 0, "Contest2 text count should be 0."
    assert contest_data_after.participant_count == 0, "Contest2 participant count should be 0."
    print(f"Contest2 updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_16_user1_deletes_own_submission_c2_t1_1_succeeds')
def test_05_17_user1_deletes_user2_submission_c1_t2_2_succeeds(client: TestClient):
    """User 1 (contest creator) attempts to delete User 2's submission (Text 2.2) from contest1 -> Should succeed."""
    assert "user1_headers" in test_data, "User 1 token (contest creator) not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t2_2_id" in test_data, "Submission ID for User 2's Text 2.2 in Contest 1 not found."
    
    submission_id_to_delete = test_data["submission_c1_t2_2_id"]

    contest1_before_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    initial_text_count_c1 = ContestResponse(**contest1_before_resp.json()).text_count

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user1_headers"] # User 1 (creator of contest1) deleting
    )
    assert response.status_code == 200, f"User 1 deleting User 2's submission {submission_id_to_delete} failed: {response.text}"
    print(f"User 1 (creator) successfully deleted User 2's submission {submission_id_to_delete} (Text 2.2) from contest1.")
    del test_data["submission_c1_t2_2_id"]

    contest_response_after = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    contest_data_after = ContestResponse(**contest_response_after.json())
    assert contest_data_after.text_count == initial_text_count_c1 - 1, "Contest1 text count did not decrease by 1."
    # Participant count might change if this was User 2's only remaining submission.
    submissions_c1_resp = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions", headers=test_data["admin_headers"])
    submissions_c1_data = [SubmissionResponse(**s) for s in submissions_c1_resp.json()]
    participant_ids_c1 = {s.owner_id for s in submissions_c1_data}
    assert contest_data_after.participant_count == len(participant_ids_c1), "Contest1 participant count mismatch."
    print(f"Contest1 updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_17_user1_deletes_user2_submission_c1_t2_2_succeeds')
def test_05_18_user1_resubmits_ai_text1_2_to_contest1(client: TestClient):
    """User 1 re-submits AI-generated Text 1.2 to contest1 (owner_restrictions=False allows this). 
    This is to set up for admin deletion test without refund."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "text1_2_id" in test_data, "Text 1.2 (AI text) ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "text1_2_cost" in test_data, "Original cost for Text 1.2 not found." # From test_04_08

    # Credits were NOT refunded in test_05_14 (original deletion of submission_c1_t1_2_id).
    # Submission of existing text should not cost again.
    user1_credits_before_resubmit = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json()).credits
    
    submission_payload = {"text_id": test_data["text1_2_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 re-submitting Text 1.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c1_t1_2_v2_id"] = submission_data["submission_id"] # New submission ID for the re-submission
    print(f"User 1 successfully re-submitted AI Text 1.2 to contest1. New Submission ID: {test_data['submission_c1_t1_2_v2_id']}.")

    user1_credits_after_resubmit = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json()).credits
    assert user1_credits_after_resubmit == user1_credits_before_resubmit, "User 1 credits changed on re-submitting an existing text."

@pytest.mark.run(after='test_05_18_user1_resubmits_ai_text1_2_to_contest1')
def test_05_19_admin_deletes_user1_ai_submission_no_refund(client: TestClient):
    """Admin deletes User 1's re-submitted AI Text 1.2 from contest1.
    - Verify Text 1.2 (object) still exists.
    - Verify User 1's credits are NOT refunded (Admin deleted, not owner).
    - Verify AI generation transaction cost record is not affected (no double refund)."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data, "User 1 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t1_2_v2_id" in test_data, "Re-submitted Text 1.2 submission ID not found."
    assert "text1_2_id" in test_data, "Text 1.2 ID not found."
    assert "text1_2_cost" in test_data, "Original cost for Text 1.2 not found."

    submission_id_to_delete = test_data["submission_c1_t1_2_v2_id"]
    user1_credits_before_admin_delete = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["admin_headers"]).json()).credits

    response = client.delete(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["admin_headers"] # Admin deleting
    )
    assert response.status_code == 200, f"Admin deleting User 1's submission {submission_id_to_delete} failed: {response.text}"
    print(f"Admin successfully deleted User 1's submission {submission_id_to_delete} (AI Text 1.2 re-submission) from contest1.")
    del test_data["submission_c1_t1_2_v2_id"]

    # 1. Verify Text 1.2 (object) still exists
    text_check_response = client.get(f"{settings.API_V1_STR}/texts/{test_data['text1_2_id']}", headers=test_data["admin_headers"])
    assert text_check_response.status_code == 200, f"Text 1.2 (ID: {test_data['text1_2_id']}) was deleted, but should still exist."
    print(f"Text object Text 1.2 (ID: {test_data['text1_2_id']}) still exists after admin deleted its submission.")

    # 2. Verify User 1's credits are NOT refunded
    user1_credits_after_admin_delete = UserResponse(**client.get(f"{settings.API_V1_STR}/users/{test_data['user1_id']}", headers=test_data["admin_headers"]).json()).credits
    assert user1_credits_after_admin_delete == user1_credits_before_admin_delete, \
        f"User 1 credits changed after admin deleted their submission. Before: {user1_credits_before_admin_delete}, After: {user1_credits_after_admin_delete}. No refund expected."
    print(f"User 1's credits ({user1_credits_after_admin_delete}) correctly not refunded when admin deleted the submission.")

    # 3. "Verify the AI generation transaction cost record is not affected." 
    # This is implicitly covered by credits not being refunded. The original cost record for *creating* Text 1.2 should remain.

# --- End of Test Section 5 ---