# backend/tests/e2e_sec_05_text_submission.py
import pytest
from httpx import AsyncClient # MODIFIED: For async client
import logging

from app.schemas.contest import ContestDetailResponse # MODIFIED: For submission data
from app.schemas.user import UserResponse # For credit checks
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 5: Text Submission Phase (Contest Open) ---

async def test_05_01_user2_submits_text2_1_to_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 submits Text 2.1 to contest1. Verify success."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_1_id" in test_data, "Text 2.1 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_1_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.1 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    # Store the submission ID as per test plan
    test_data["submission_id_c1_t2_1"] = submission_data["submission_id"]
    assert test_data["submission_id_c1_t2_1"] is not None
    print(f"User 2 successfully submitted Text 2.1 (ID: {test_data['text2_1_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_id_c1_t2_1']}.")

@pytest.mark.run(after='test_05_01_user2_submits_text2_1_to_contest1')
async def test_05_02_user2_submits_text2_2_to_contest1_and_verify_counts(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 submits Text 2.2 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_2_id" in test_data, "Text 2.2 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_2_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t2_2_id"] = submission_data["submission_id"]
    print(f"User 2 successfully submitted Text 2.2 (ID: {test_data['text2_2_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t2_2_id']}.")

    contest_response = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 3, f"Expected 3 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_02_user2_submits_text2_2_to_contest1_and_verify_counts')
async def test_05_03_user1_submits_text1_2_to_contest1_and_verify_counts(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 submits Text 1.2 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_2_id" in test_data, "Text 1.2 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text1_2_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t1_2_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.2 (ID: {test_data['text1_2_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t1_2_id']}.")

    contest_response = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 4, f"Expected 4 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_03_user1_submits_text1_2_to_contest1_and_verify_counts')
async def test_05_04_user1_submits_text1_3_to_contest1_and_verify_counts(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 submits Text 1.3 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.3 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t1_3_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.3 (ID: {test_data['text1_3_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t1_3_id']}.")

    contest_response = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 5, f"Expected 5 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_04_user1_submits_text1_3_to_contest1_and_verify_counts')
async def test_05_05_user2_submits_text2_3_to_contest1_and_verify_counts(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 submits Text 2.3 to contest1. Verify success.
    - Verify contest1 shows updated text count and participant count."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "text2_3_id" in test_data, "Text 2.3 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    submission_payload = {"text_id": test_data["text2_3_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"]
    )
    assert response.status_code in [200, 201], f"User 2 submitting Text 2.3 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c1_t2_3_id"] = submission_data["submission_id"]
    print(f"User 2 successfully submitted Text 2.3 (ID: {test_data['text2_3_id']}) to contest1 (ID: {test_data['contest1_id']}). Submission ID: {test_data['submission_c1_t2_3_id']}.")

    contest_response = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    assert contest_response.status_code == 200, f"Failed to get contest1 details: {contest_response.text}"
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 6, f"Expected 6 texts in contest1, got {contest_data.text_count}"
    assert contest_data.participant_count == 2, f"Expected 2 participants in contest1, got {contest_data.participant_count}"
    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data.text_count}, participant count: {contest_data.participant_count}.")

@pytest.mark.run(after='test_05_05_user2_submits_text2_3_to_contest1_and_verify_counts')
async def test_05_06_user1_submits_text1_1_to_contest2_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 submits Text 1.1 to contest2. Verify success (owner_restrictions=True, first submission)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    # Verify Contest 2 settings: owner_restrictions = True
    contest_resp = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR, Admin can view full details
    assert contest_resp.status_code == 200
    contest_details = ContestDetailResponse(**contest_resp.json())
    assert contest_details.author_restrictions is True, "Contest 2 author_restrictions should be True for this test."

    submission_payload = {"text_id": test_data["text1_1_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"],
        params={"password": test_data["contest2_password"]}
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.1 to contest2 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data, "Submission response missing submission_id."
    test_data["submission_c2_t1_1_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.1 (ID: {test_data['text1_1_id']}) to contest2 (ID: {test_data['contest2_id']}). Submission ID: {test_data['submission_c2_t1_1_id']}.")

    contest_response_after = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    contest_data_after = ContestDetailResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, f"Expected 1 text in contest2, got {contest_data_after.text_count}"
    assert contest_data_after.participant_count == 1, f"Expected 1 participant in contest2, got {contest_data_after.participant_count}"
    print(f"Contest2 (ID: {test_data['contest2_id']}) updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_06_user1_submits_text1_1_to_contest2_succeeds')
async def test_05_07_user1_submits_text1_3_to_contest2_fails(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 attempts to submit Text 1.3 to contest2 -> Fails due to author_restrictions."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID not found." # User1's other manual text
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "submission_c2_t1_1_id" in test_data, "User 1's first submission to contest2 not found."

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"],
        params={"password": test_data["contest2_password"]}
    )
    assert response.status_code == 403, f"User 1 submitting second text to contest2 (author_restrictions=True) should fail (403), but got {response.status_code}: {response.text}"
    assert "one submission per author" in response.text # Keep check for detail message
    print("User 1 attempt to submit a second text (Text 1.3) to contest2 failed as expected due to author_restrictions.")

    contest_response_after = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    contest_data_after = ContestDetailResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, "Text count for contest2 should remain 1."
    assert contest_data_after.participant_count == 1, "Participant count for contest2 should remain 1."

@pytest.mark.run(after='test_05_07_user1_submits_text1_3_to_contest2_fails')
async def test_05_08_user2_submits_text2_3_to_contest2_fails_judge_restriction(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 attempts to submit Text 2.3 to contest2 -> Fails due to judge_restrictions."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "text2_3_id" in test_data, "Text 2.3 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    # Verify Contest 2 settings and User 2 is a judge
    contest_resp = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_resp.status_code == 200
    contest_details = ContestDetailResponse(**contest_resp.json())
    assert contest_details.judge_restrictions is True, "Contest 2 judge_restrictions should be True."
    is_judge = False
    if hasattr(contest_details, 'judges') and contest_details.judges: # Check if attribute exists and is not empty
        is_judge = any(str(judge.user_judge_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_judge_id)
    assert is_judge, "User 2 is not listed as a judge for contest2 for this test (or judges relationship not loaded)." # Updated assertion message

    submission_payload = {"text_id": test_data["text2_3_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user2_headers"],
        params={"password": test_data["contest2_password"]}
    )
    assert response.status_code == 403, f"User 2 (judge) submitting to contest2 (judge_restrictions=True) should fail (403), got {response.status_code}: {response.text}"
    print("User 2 (judge) attempt to submit Text 2.3 to contest2 failed as expected due to judge_restrictions.")

    contest_response_after = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    contest_data_after = ContestDetailResponse(**contest_response_after.json())
    assert contest_data_after.text_count == 1, "Text count for contest2 should remain 1 after failed judge submission."

@pytest.mark.run(after='test_05_08_user2_submits_text2_3_to_contest2_fails_judge_restriction')
async def test_05_09_admin_submits_text3_2_to_contest1_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin submits AI-generated Text 3.2 to contest1. Verify success."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "text3_2_id" in test_data, "Text 3.2 (Admin's AI text) ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    contest1_before_resp = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    contest1_before_data = ContestDetailResponse(**contest1_before_resp.json())
    initial_text_count_c1 = contest1_before_data.text_count
    initial_participant_count_c1 = contest1_before_data.participant_count

    submission_payload = {"text_id": test_data["text3_2_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["admin_headers"]
    )
    assert response.status_code in [200, 201], f"Admin submitting Text 3.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c1_t3_2_id"] = submission_data["submission_id"]
    print(f"Admin successfully submitted AI Text 3.2 to contest1. Submission ID: {test_data['submission_c1_t3_2_id']}.")

    contest_response_after = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    contest_data_after = ContestDetailResponse(**contest_response_after.json())
    assert contest_data_after.text_count == initial_text_count_c1 + 1
    # Admin is a new participant if they haven't submitted before, or participant count stays same if admin is user1 or user2.
    # Assuming admin is a distinct user.
    # If admin is user1 or user2 who already submitted, participant count might not increase by 1.
    # Need to check if admin_user_id is in list of participant_ids for contest1_before_data to be more precise.
    # For now, we assume admin is a new participant.
    initial_participant_ids = set()
    if hasattr(contest1_before_data, 'participants') and contest1_before_data.participants:
        initial_participant_ids = {p.user_id for p in contest1_before_data.participants if hasattr(p, 'user_id') and p.user_id}

    if test_data.get("admin_user_id") not in initial_participant_ids:
         assert contest_data_after.participant_count == initial_participant_count_c1 + 1, \
             f"Expected participant count to be {initial_participant_count_c1 + 1}, but got {contest_data_after.participant_count}"
    else:
         assert contest_data_after.participant_count == initial_participant_count_c1, \
                f"Expected participant count to be {initial_participant_count_c1}, but got {contest_data_after.participant_count}"

    print(f"Contest1 (ID: {test_data['contest1_id']}) updated text count: {contest_data_after.text_count}, participant count: {contest_data_after.participant_count}.")

@pytest.mark.run(after='test_05_09_admin_submits_text3_2_to_contest1_succeeds')
async def test_05_10_user1_views_submissions_contest1_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User1 is contest1 owner, should be able to view submissions."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = await client.get( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 (owner) viewing submissions for contest1 failed: {response.text}"
    submissions = response.json()
    assert isinstance(submissions, list), "Submissions endpoint should return a list."
    # We know at least text2_1, text2_2, text1_2, text1_3, text2_3, text3_2 were submitted (6 submissions)
    # Some may have been deleted. Let's check current count via contest details
    contest_resp = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await
    current_text_count = ContestDetailResponse(**contest_resp.json()).text_count
    assert len(submissions) == current_text_count, f"Expected {current_text_count} submissions, got {len(submissions)}"
    print(f"User 1 (owner) successfully viewed {len(submissions)} submissions for contest1.")

@pytest.mark.run(after='test_05_10_user1_views_submissions_contest1_succeeds')
async def test_05_11_user2_views_submissions_contest1_fails(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User2 is a participant but not owner/judge, should not be able to view submissions."""
    assert "user2_headers" in test_data, "User 2 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = await client.get( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 403, f"User 2 (participant) viewing submissions for contest1 should fail (403), got {response.status_code}: {response.text}"
    print("User 2 (participant) attempt to view submissions for contest1 failed as expected.")

@pytest.mark.run(after='test_05_11_user2_views_submissions_contest1_fails')
async def test_05_12_visitor_views_submissions_contest1_fails(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """A visitor (no token) should not be able to view submissions."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/") # MODIFIED: await, removed settings.API_V1_STR
    assert response.status_code == 401, f"Visitor viewing submissions for contest1 should fail (401), got {response.status_code}: {response.text}" # Assuming 401 for unauthenticated
    print("Visitor attempt to view submissions for contest1 failed as expected.")

@pytest.mark.run(after='test_05_12_visitor_views_submissions_contest1_fails')
async def test_05_13_admin_views_submissions_contest1_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin should be able to view submissions for any contest."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    response = await client.get( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin viewing submissions for contest1 failed: {response.text}"
    submissions = response.json()
    assert isinstance(submissions, list)
    contest_resp = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await
    current_text_count = ContestDetailResponse(**contest_resp.json()).text_count
    assert len(submissions) == current_text_count, f"Expected {current_text_count} submissions for admin, got {len(submissions)}"
    print(f"Admin successfully viewed {len(submissions)} submissions for contest1.")
    # Store one submission_id from admin's view for deletion test by owner
    if submissions:
        for sub in submissions:
            # Try to find a submission by user1 (owner of contest1) that is AI generated
            # Assume text1_2 was AI by User1 (ID: test_data["text1_2_id"])
            if sub.get("text_id") == test_data.get("text1_2_id") and sub.get("user_id") == test_data.get("user1_id"):
                test_data["submission_c1_t1_2_ai_id_for_deletion"] = sub["submission_id"]
                print(f"Found AI submission by user1 for deletion test: {sub['submission_id']}")
                break

@pytest.mark.run(after='test_05_13_admin_views_submissions_contest1_succeeds')
async def test_05_14_user1_removes_own_ai_submission_c1_t1_2_no_refund(client: AsyncClient):
    """User 1 (owner of contest1) removes their own AI-generated submission (text1_2) from contest1.
    - Credits should NOT be refunded as it's an AI text."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t1_2_id" in test_data, "Submission ID for User 1's text1_2 in contest1 not found."
    submission_id_to_delete = test_data["submission_c1_t1_2_id"]

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    user1_data_before = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_before = user1_data_before['credits']

    contest_before_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_before_resp.status_code == 200
    contest_texts_before = ContestDetailResponse(**contest_before_resp.json()).text_count

    response = await client.delete(
        f"/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 204, f"User 1 removing own AI submission {submission_id_to_delete} from contest1 failed: {response.text}"
    print(f"User 1 successfully removed own AI submission {submission_id_to_delete} from contest1.")

    users_resp_after = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp_after.status_code == 200
    users_data_after = users_resp_after.json()
    user1_data_after = next(u for u in users_data_after if u['id'] == test_data['user1_id'])
    user1_credits_after = user1_data_after['credits']
    assert user1_credits_after == user1_credits_before, \
        f"User 1 credits should not change after removing AI submission. Before: {user1_credits_before}, After: {user1_credits_after}"

    contest_after_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_after_resp.status_code == 200
    contest_texts_after = ContestDetailResponse(**contest_after_resp.json()).text_count
    assert contest_texts_after == contest_texts_before - 1, \
        f"Contest1 text count should decrease by 1. Before: {contest_texts_before}, After: {contest_texts_after}"
    print(f"Contest1 text count updated to {contest_texts_after}. User1 credits unchanged ({user1_credits_after}).")
    if "submission_c1_t1_2_id" in test_data: del test_data["submission_c1_t1_2_id"]
    if "submission_c1_t1_2_ai_id_for_deletion" in test_data: del test_data["submission_c1_t1_2_ai_id_for_deletion"]

@pytest.mark.run(after='test_05_14_user1_removes_own_ai_submission_c1_t1_2_no_refund')
async def test_05_15_user2_removes_own_submission_c1_t2_1_succeeds(client: AsyncClient):
    """User 2 removes their own (manual) submission (text2_1) from contest1.
    - Credits might be refunded if applicable (current test plan implies no for manual text removal by owner, needs verification based on project spec if submission cost exists)."""
    assert "user2_headers" in test_data and "user2_id" in test_data, "User 2 token/ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_id_c1_t2_1" in test_data, "Submission ID for User 2's text2_1 in contest1 not found."
    submission_id_to_delete = test_data["submission_id_c1_t2_1"]
    
    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])

    
    assert users_resp.status_code == 200

    
    users_data = users_resp.json()

    
    user2_before_data = next(u for u in users_data if u['id'] == test_data['user2_id'])
    user2_credits_before = user2_before_data['credits']

    contest_before_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_before_resp.status_code == 200
    contest_texts_before = ContestDetailResponse(**contest_before_resp.json()).text_count

    response = await client.delete(
        f"/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user2_headers"]
    )
    assert response.status_code == 204, f"User 2 removing own submission {submission_id_to_delete} from contest1 failed: {response.text}"
    print(f"User 2 successfully removed own submission {submission_id_to_delete} from contest1.")

    users_resp_after = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp_after.status_code == 200
    users_data_after = users_resp_after.json()
    user2_after_data = next(u for u in users_data_after if u['id'] == test_data['user2_id'])
    user2_credits_after = user2_after_data['credits']
    # Project spec: "Un dueño puede en cualquier momento retirar un texto suyo." - no mention of credit refund for manual text submission removal.
    # Test plan implies no refund or doesn't specify. Let's assume no refund for now unless submission had a cost.
    # If submitting a manual text cost credits, a refund might be expected.
    # For now, assuming submission itself (not AI generation) is free.
    assert user2_credits_after == user2_credits_before, \
        f"User 2 credits should ideally not change after removing manual submission unless submission itself had a cost. Before: {user2_credits_before}, After: {user2_credits_after}"

    contest_after_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_after_resp.status_code == 200
    contest_texts_after = ContestDetailResponse(**contest_after_resp.json()).text_count
    assert contest_texts_after == contest_texts_before - 1, \
        f"Contest1 text count should decrease by 1. Before: {contest_texts_before}, After: {contest_texts_after}"
    print(f"Contest1 text count updated to {contest_texts_after}. User2 credits unchanged ({user2_credits_after}).")
    if "submission_id_c1_t2_1" in test_data: del test_data["submission_id_c1_t2_1"]

@pytest.mark.run(after='test_05_15_user2_removes_own_submission_c1_t2_1_succeeds')
async def test_05_16_user1_removes_own_submission_c2_t1_1_succeeds(client: AsyncClient):
    """User 1 (owner of text1_1) removes their submission from contest2.
    - contest2 had author_restrictions=True, this was user1's only submission there."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "submission_c2_t1_1_id" in test_data, "Submission ID for User 1's text1_1 in contest2 not found."
    submission_id_to_delete = test_data["submission_c2_t1_1_id"]

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_before_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_before = user1_before_data['credits']

    contest2_before_resp = await client.get(
        f"/contests/{test_data['contest2_id']}", 
        headers=test_data["user1_headers"], 
        params={"password": test_data["contest2_password"]}
    ) # MODIFIED: Added user1_headers and password to view private contest
    assert contest2_before_resp.status_code == 200 # Now this should pass
    contest2_data_before = ContestDetailResponse(**contest2_before_resp.json())
    contest2_texts_before = contest2_data_before.text_count
    contest2_participants_before = contest2_data_before.participant_count

    response = await client.delete(
        f"/contests/{test_data['contest2_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user1_headers"],
        params={"password": test_data["contest2_password"]}
    )
    assert response.status_code == 204, f"User 1 removing submission {submission_id_to_delete} from contest2 failed: {response.text}"
    print(f"User 1 successfully removed submission {submission_id_to_delete} from contest2.")

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_after_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_after = user1_after_data['credits']
    assert user1_credits_after == user1_credits_before, \
        f"User 1 credits should not change. Before: {user1_credits_before}, After: {user1_credits_after}"

    contest2_after_resp = await client.get(
        f"/contests/{test_data['contest2_id']}", 
        headers=test_data["user1_headers"], 
        params={"password": test_data["contest2_password"]}
    ) # MODIFIED: Added user1_headers and password
    assert contest2_after_resp.status_code == 200
    contest2_data_after = ContestDetailResponse(**contest2_after_resp.json())
    assert contest2_data_after.text_count == contest2_texts_before - 1, "Contest2 text count should decrease by 1."
    assert contest2_data_after.participant_count == contest2_participants_before - 1, "Contest2 participant count should decrease by 1."
    print(f"Contest2 counts updated. User1 credits unchanged ({user1_credits_after}).")
    if "submission_c2_t1_1_id" in test_data: del test_data["submission_c2_t1_1_id"]

@pytest.mark.run(after='test_05_16_user1_removes_own_submission_c2_t1_1_succeeds')
async def test_05_17_user1_removes_user2_submission_c1_t2_2_succeeds(client: AsyncClient):
    """User 1 (owner of contest1) removes User 2's submission (text2_2) from contest1.
    - No credit refund to User 2 as removal is by contest owner."""
    assert "user1_headers" in test_data, "User 1 (contest owner) token not found."
    assert "user2_id" in test_data, "User 2 ID (submitter) not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t2_2_id" in test_data, "Submission ID for User 2's text2_2 in contest1 not found."
    submission_id_to_delete = test_data["submission_c1_t2_2_id"]

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    user2_before_data = next(u for u in users_data if u['id'] == test_data['user2_id'])
    user2_credits_before = user2_before_data['credits']

    contest1_before_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest1_before_resp.status_code == 200
    contest1_texts_before = ContestDetailResponse(**contest1_before_resp.json()).text_count

    response = await client.delete(
        f"/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["user1_headers"] # User1 (owner) deleting
    )
    assert response.status_code == 204, f"User 1 removing User 2's submission {submission_id_to_delete} from contest1 failed: {response.text}"
    print(f"User 1 successfully removed User 2's submission {submission_id_to_delete} from contest1.")

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user2_after_data = next(u for u in users_data if u['id'] == test_data['user2_id'])
    user2_credits_after = user2_after_data['credits']
    assert user2_credits_after == user2_credits_before, \
        f"User 2 credits should not change. Before: {user2_credits_before}, After: {user2_credits_after}"

    contest1_after_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest1_after_resp.status_code == 200
    contest1_texts_after = ContestDetailResponse(**contest1_after_resp.json()).text_count
    assert contest1_texts_after == contest1_texts_before - 1, \
        f"Contest1 text count should decrease by 1. Before: {contest1_texts_before}, After: {contest1_texts_after}"
    print(f"Contest1 text count updated to {contest1_texts_after}. User2 credits unchanged ({user2_credits_after}).")

@pytest.mark.run(after='test_05_17_user1_removes_user2_submission_c1_t2_2_succeeds')
async def test_05_18_user1_resubmits_ai_text1_2_to_contest1(client: AsyncClient):
    """User 1 re-submits AI Text 1.2 to contest1 after it was deleted.
    - Should succeed. Cost should be 0 as it's AI text."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "text1_2_id" in test_data, "Text 1.2 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    # submission_c1_t1_2_id was deleted, so this is a new submission of the same text

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_before_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_before = user1_before_data['credits']

    contest_before_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_before_resp.status_code == 200
    contest_texts_before = ContestDetailResponse(**contest_before_resp.json()).text_count

    submission_payload = {"text_id": test_data["text1_2_id"]}
    response = await client.post( # MODIFIED: await, removed settings.API_V1_STR
        f"/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 re-submitting AI Text 1.2 to contest1 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c1_t1_2_resubmitted_id"] = submission_data["submission_id"] # New ID
    print(f"User 1 successfully re-submitted AI Text 1.2 to contest1. New Submission ID: {submission_data['submission_id']}.")

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_after_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_after = user1_after_data['credits']
    assert user1_credits_after == user1_credits_before, \
        f"User 1 credits should not change for AI text resubmission. Before: {user1_credits_before}, After: {user1_credits_after}"

    contest_after_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest_after_resp.status_code == 200
    contest_texts_after = ContestDetailResponse(**contest_after_resp.json()).text_count
    assert contest_texts_after == contest_texts_before + 1, \
        f"Contest1 text count should increase by 1. Before: {contest_texts_before}, After: {contest_texts_after}"
    print(f"Contest1 text count updated to {contest_texts_after}. User1 credits unchanged ({user1_credits_after}).")

@pytest.mark.run(after='test_05_18_user1_resubmits_ai_text1_2_to_contest1')
async def test_05_19_admin_removes_user1_ai_submission_no_refund(client: AsyncClient):
    """Admin removes User 1's re-submitted AI text (submission_c1_t1_2_resubmitted_id) from contest1.
    - No credit refund to User 1."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data, "User 1 ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "submission_c1_t1_2_resubmitted_id" in test_data, "Resubmitted AI submission ID not found."
    submission_id_to_delete = test_data["submission_c1_t1_2_resubmitted_id"]

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_before_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_before = user1_before_data['credits']

    contest1_before_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest1_before_resp.status_code == 200
    contest1_texts_before = ContestDetailResponse(**contest1_before_resp.json()).text_count

    response = await client.delete(
        f"/contests/{test_data['contest1_id']}/submissions/{submission_id_to_delete}",
        headers=test_data["admin_headers"] # Admin removing
    )
    assert response.status_code == 204, f"Admin removing User 1's AI submission {submission_id_to_delete} failed: {response.text}"
    print(f"Admin successfully removed User 1's AI submission {submission_id_to_delete} from contest1.")

    users_resp = await client.get("/admin/users", headers=test_data["admin_headers"])


    assert users_resp.status_code == 200


    users_data = users_resp.json()


    user1_after_data = next(u for u in users_data if u['id'] == test_data['user1_id'])
    user1_credits_after = user1_after_data['credits']
    assert user1_credits_after == user1_credits_before, \
        f"User 1 credits should not change. Before: {user1_credits_before}, After: {user1_credits_after}"

    contest1_after_resp = await client.get(f"/contests/{test_data['contest1_id']}")
    assert contest1_after_resp.status_code == 200
    contest1_texts_after = ContestDetailResponse(**contest1_after_resp.json()).text_count
    assert contest1_texts_after == contest1_texts_before - 1, \
        f"Contest1 text count should decrease by 1. Before: {contest1_texts_before}, After: {contest1_texts_after}"
    print(f"Contest1 text count updated to {contest1_texts_after}. User1 credits unchanged ({user1_credits_after}).")
    if "submission_c1_t1_2_resubmitted_id" in test_data: del test_data["submission_c1_t1_2_resubmitted_id"]

@pytest.mark.run(after='test_05_19_admin_removes_user1_ai_submission_no_refund')
async def test_05_20_user1_submits_text1_1_to_contest3(client: AsyncClient):
    """User 1 submits Text 1.1 to contest3. Verify success."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    # Ensure contest3 is open - it should be by default upon creation
    # Optional: Add a check if contest3 status is 'OPEN'

    submission_payload = {"text_id": test_data["text1_1_id"]}
    response = await client.post(
        f"/contests/{test_data['contest3_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.1 to contest3 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c3_t1_1_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.1 (ID: {test_data['text1_1_id']}) to contest3 (ID: {test_data['contest3_id']}). Submission ID: {test_data['submission_c3_t1_1_id']}.")

    # Verify contest details
    contest_response = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response.status_code == 200
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 1
    assert contest_data.participant_count == 1
    print(f"Contest3 (ID: {test_data['contest3_id']}) has 1 text and 1 participant.")

@pytest.mark.run(after='test_05_20_user1_submits_text1_1_to_contest3')
async def test_05_21_user1_resubmits_text1_1_to_contest3_fails(client: AsyncClient):
    """User 1 tries to submit Text 1.1 again to contest3 -> Fails because the text is already submitted."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "submission_c3_t1_1_id" in test_data, "Initial submission of Text 1.1 to contest3 not found."

    submission_payload = {"text_id": test_data["text1_1_id"]}
    response = await client.post(
        f"/contests/{test_data['contest3_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    # Expecting a 409 Conflict or similar error indicating the text is already submitted.
    # The exact status code might depend on API implementation for this specific case.
    # Let's assume 400 Bad Request or 409 Conflict for "already submitted"
    assert response.status_code in [400, 409], f"User 1 re-submitting Text 1.1 to contest3 should fail (400/409), but got {response.status_code}: {response.text}"
    print(f"User 1 attempt to re-submit Text 1.1 to contest3 failed as expected ({response.status_code}).")

    # Verify contest counts haven't changed
    contest_response = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response.status_code == 200
    contest_data = ContestDetailResponse(**contest_response.json())
    assert contest_data.text_count == 1, "Text count for contest3 should remain 1 after failed re-submission."
    assert contest_data.participant_count == 1, "Participant count for contest3 should remain 1 after failed re-submission."

@pytest.mark.run(after='test_05_21_user1_resubmits_text1_1_to_contest3_fails')
async def test_05_22_user1_removes_and_resubmits_text1_1_to_contest3_succeeds(client: AsyncClient):
    """User 1 removes Text 1.1 from contest3, then submits it again. Succeeds."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "submission_c3_t1_1_id" in test_data, "Submission ID for Text 1.1 in contest3 not found."

    # Step 1: Remove the submission
    submission_id_to_remove = test_data["submission_c3_t1_1_id"]
    delete_response = await client.delete(
        f"/contests/{test_data['contest3_id']}/submissions/{submission_id_to_remove}",
        headers=test_data["user1_headers"]  # User 1 is the owner of the text and submitted it
    )
    assert delete_response.status_code == 204, f"User 1 removing submission {submission_id_to_remove} from contest3 failed: {delete_response.text}"
    print(f"User 1 successfully removed submission (ID: {submission_id_to_remove}) of Text 1.1 from contest3.")

    # Verify contest counts after removal
    contest_response_after_delete = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response_after_delete.status_code == 200
    contest_data_after_delete = ContestDetailResponse(**contest_response_after_delete.json())
    assert contest_data_after_delete.text_count == 0, "Text count for contest3 should be 0 after removal."
    # Participant count might remain 1 if the user has other texts or if it's not decremented until all texts by user are removed.
    # Let's assume it becomes 0 if this was the only text by the user. This depends on specific business logic.
    # For now, let's be flexible or focus on text_count. The plan doesn't specify participant count change here.
    # A safer bet is to check text_count.

    # Step 2: Re-submit Text 1.1 to contest3
    submission_payload = {"text_id": test_data["text1_1_id"]}
    resubmit_response = await client.post(
        f"/contests/{test_data['contest3_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert resubmit_response.status_code in [200, 201], f"User 1 re-submitting Text 1.1 to contest3 after removal failed: {resubmit_response.text}"
    new_submission_data = resubmit_response.json()
    assert "submission_id" in new_submission_data
    test_data["submission_c3_t1_1_id_v2"] = new_submission_data["submission_id"] # Store new submission ID
    print(f"User 1 successfully re-submitted Text 1.1 to contest3. New Submission ID: {test_data['submission_c3_t1_1_id_v2']}.")

    # Verify contest counts after re-submission
    contest_response_after_resubmit = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response_after_resubmit.status_code == 200
    contest_data_after_resubmit = ContestDetailResponse(**contest_response_after_resubmit.json())
    assert contest_data_after_resubmit.text_count == 1, "Text count for contest3 should be 1 after re-submission."
    assert contest_data_after_resubmit.participant_count == 1, "Participant count for contest3 should be 1 after re-submission."

@pytest.mark.run(after='test_05_22_user1_removes_and_resubmits_text1_1_to_contest3_succeeds')
async def test_05_23_user1_submits_text1_4_to_contest3(client: AsyncClient):
    """User 1 submits Text 1.4 to contest3."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_4_id" in test_data, "Text 1.4 ID not found (should be created in Section 4.16)."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    # Get current contest counts
    contest_response_before = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response_before.status_code == 200
    contest_data_before = ContestDetailResponse(**contest_response_before.json())
    initial_text_count = contest_data_before.text_count
    # initial_participant_count = contest_data_before.participant_count # User 1 is already a participant

    submission_payload = {"text_id": test_data["text1_4_id"]}
    response = await client.post(
        f"/contests/{test_data['contest3_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [200, 201], f"User 1 submitting Text 1.4 to contest3 failed: {response.text}"
    submission_data = response.json()
    assert "submission_id" in submission_data
    test_data["submission_c3_t1_4_id"] = submission_data["submission_id"]
    print(f"User 1 successfully submitted Text 1.4 (ID: {test_data['text1_4_id']}) to contest3 (ID: {test_data['contest3_id']}). Submission ID: {test_data['submission_c3_t1_4_id']}.")

    # Verify contest counts after submission
    contest_response_after = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_response_after.status_code == 200
    contest_data_after = ContestDetailResponse(**contest_response_after.json())
    assert contest_data_after.text_count == initial_text_count + 1, f"Text count for contest3 should be {initial_text_count + 1} after submitting Text 1.4."
    # Participant count should not change as User 1 was already a participant from Text 1.1
    assert contest_data_after.participant_count == 1, "Participant count for contest3 should remain 1 as User 1 is the same participant."

# --- End of Test Section 5 ---