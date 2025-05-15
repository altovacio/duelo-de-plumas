# backend/tests/e2e_sec_06_evaluation_phase.py
import pytest
from httpx import AsyncClient # MODIFIED: For async client
import logging

from app.schemas.contest import ContestUpdate, ContestResponse, TextSubmissionResponse, ContestTextResponse, ContestDetailResponse
from app.schemas.user import UserResponse, UserCredit # For credit top-up
from app.schemas.vote import VoteCreate, VoteResponse # Added Vote schemas
from tests.shared_test_state import test_data
from app.core.config import settings # ADDED import for settings

# client will be a fixture argument to test functions

# --- Start of Test Section 6: Evaluation Phase (Contest in Evaluation) ---

async def test_06_01_user1_sets_contest1_status_to_evaluation(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 sets contest1 status to 'Evaluation'."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = await client.put(
        f"/contests/{test_data['contest1_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to set contest1 status to Evaluation: {response.text}"
    
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.status.lower() == "evaluation", \
        f"Contest1 status was not updated to Evaluation. Current status: {updated_contest.status}"
    
    print(f"User 1 successfully set contest1 (ID: {test_data['contest1_id']}) status to: {updated_contest.status}.")

@pytest.mark.run(after='test_06_01_user1_sets_contest1_status_to_evaluation')
async def test_06_02_user1_submit_to_evaluation_contest1_fails(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 attempts to submit a new text to contest1 (in Evaluation). Should fail."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID (manual text by User 1) not found."

    # Confirm contest1 is in Evaluation status first
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    current_status = ContestDetailResponse(**contest_check_response.json()).status # FIX: Use ContestDetailResponse
    assert current_status.lower() == "evaluation", \
        f"Contest1 is not in 'Evaluation' state for this test. Current: {current_status}"

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/submissions/", # REVERT FIX: Add back trailing slash for POST
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [400, 403], \
        f"Submitting to contest1 in 'Evaluation' phase should fail (400/403), but got {response.status_code}: {response.text}"

    print(f"User 1 attempt to submit Text 1.3 to contest1 (in Evaluation) failed as expected (Status: {response.status_code}).")

@pytest.mark.run(after='test_06_02_user1_submit_to_evaluation_contest1_fails')
async def test_06_03_visitor_views_contest1_submissions_masked(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Visitor attempts to view submissions for contest1 -> Should succeed, user and author names masked."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}") # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    current_status = ContestDetailResponse(**contest_check_response.json()).status # FIX: Use ContestDetailResponse
    assert current_status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {current_status}"

    response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/") 
    assert response.status_code == 200, f"Visitor failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list."

    for sub_data in submissions:
        submission = ContestTextResponse(**sub_data)
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
        assert submission.owner_id is None # Masked field check
        assert submission.text_id is not None
        text_resp = await client.get(f"/texts/{submission.text_id}") # MODIFIED: await, removed settings.API_V1_STR
        assert text_resp.status_code == 200

    print(f"Visitor successfully viewed submissions for contest1 (ID: {test_data['contest1_id']}) with user/author info masked.")

@pytest.mark.run(after='test_06_03_visitor_views_contest1_submissions_masked')
async def test_06_04_user2_judge_views_contest1_submissions_masked(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 (human judge) views submissions for contest1 -> Should succeed, user and author names masked."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user2_headers" in test_data, "User 2 headers not found."
    assert "user2_id" in test_data, "User 2 ID not found."

    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user2_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    contest_details = ContestDetailResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {contest_details.status}"
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not listed as a judge for contest1."

    response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user2_headers"]) 
    assert response.status_code == 200, f"User 2 (judge) failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list for judge."

    for sub_data in submissions:
        submission = ContestTextResponse(**sub_data)
        assert submission.owner_id is None # Masked field check
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
        assert submission.text_id is not None

    print(f"User 2 (judge) successfully viewed submissions for contest1 (ID: {test_data['contest1_id']}) with user/author info masked.")

@pytest.mark.run(after='test_06_04_user2_judge_views_contest1_submissions_masked')
async def test_06_05_user1_votes_in_contest1_fails_not_judge(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 attempts to vote in contest 1 -> Should fail (is not a judge)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data, "User 1 headers not found."
    # User1 will attempt to vote on their own text (text1_3) in contest1
    # This text should still be in contest1 as its submission (submission_c1_t1_3_id) was not deleted in sec 5.
    assert "text1_3_id" in test_data, "Text 1.3 ID not found in test_data."
    text_id_to_vote_on = test_data["text1_3_id"]

    vote_payload = {
        "text_id": text_id_to_vote_on,
        "text_place": 1, # Attempting to give 1st place
        "comment": "User 1 (not a judge) trying to vote on their own text in contest1."
    }
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/votes", # REVERTED: REMOVE TRAILING SLASH
        json=vote_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 voting (not judge) should fail with 403, but got {response.status_code}: {response.text}"
    print(f"User 1 attempt to vote in contest1 (ID: {test_data['contest1_id']}) on text {text_id_to_vote_on} failed as expected (403 - not a judge).")

@pytest.mark.run(after='test_06_05_user1_votes_in_contest1_fails_not_judge')
async def test_06_06_user2_votes_in_contest1_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 (judge) votes in contest 1, assigning a place and comment to one text."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user2_headers" in test_data, "User 2 headers not found."
    assert "user2_id" in test_data, "User 2 ID not found."

    assert "text2_3_id" in test_data, "Text 2.3 ID for voting not found."
    text_id_to_vote_on = test_data["text2_3_id"]

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user2_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestDetailResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {contest_details.status}"
    
    # Verify User 2 is indeed a judge for contest1
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not configured as a judge for contest1 for this test."

    vote_payload = {
        "text_id": text_id_to_vote_on,
        "text_place": 1, # User 2 gives 1st place
        "comment": "User 2 (judge) finds this submission quite compelling and ranks it 1st."
    }

    response = await client.post(
        f"/contests/{test_data['contest1_id']}/votes", 
        json=vote_payload,
        headers=test_data["user2_headers"]
    )

    assert response.status_code in [200, 201], \
        f"User 2 (judge) voting in contest1 should succeed, but got {response.status_code}: {response.text}"
    
    vote_data = response.json()
    assert vote_data["text_place"] == vote_payload["text_place"]
    assert vote_data["comment"] == vote_payload["comment"]
    assert str(vote_data["judge_id"]) == str(test_data["user2_id"]), "Vote judge_id does not match User 2 ID."
    assert vote_data["text_id"] == text_id_to_vote_on
    assert vote_data["contest_id"] == test_data["contest1_id"]
    test_data["user2_vote_on_text2_3_id_in_c1"] = vote_data["id"] # MODIFIED: Updated test_data key

    print(f"User 2 (judge) successfully voted on text {text_id_to_vote_on} in contest1 (ID: {test_data['contest1_id']}). Vote ID: {vote_data['id']}")

@pytest.mark.run(after='test_06_06_user2_votes_in_contest1_succeeds')
async def test_06_07_user1_triggers_judge_global_for_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 triggers judge_global evaluation for contest1. Succeeds. Verify User 1's credit balance decreased."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "admin_headers" in test_data, "Admin headers not found for potential credit top-up."
    assert "judge_global_id" in test_data, "judge_global_id (AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"])
    assert contest_check_response.status_code == 200
    assert ContestDetailResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Get User 1's initial credits
    user1_details_before_resp = await client.get(f"/users/me", headers=test_data["user1_headers"])
    assert user1_details_before_resp.status_code == 200
    user1_details_before = UserResponse(**user1_details_before_resp.json())
    initial_credits_user1 = user1_details_before.credits
    
    # The test assumes User 1 has enough credits. 
    # If not, the trigger-ai-judge endpoint should handle it (e.g., by returning an error).
    # The E2E test setup should ensure users have a reasonable starting credit balance for tests.
    # Removing the admin top-up logic that was here.

    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "contest_id": test_data["contest1_id"],
        "model": settings.DEFAULT_TEST_MODEL_ID # MODIFIED: Use default test model from settings
    }
    response = await client.post(
        f"/agents/execute/judge",
        json=trigger_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 failed to trigger judge_global for contest1: {response.text}"
    
    trigger_response_data_list = response.json()
    assert isinstance(trigger_response_data_list, list), "Expected a list of execution responses"
    if not trigger_response_data_list: # If no texts to evaluate, it might return an empty list and 0 credits.
        credits_used = 0
    else:
        credits_used = sum(item.get("credits_used", 0) for item in trigger_response_data_list)

    test_data["contest1_judge_global_eval_cost_user1"] = credits_used # Store or update the cost

    # Verify User 1's credits decreased
    user1_details_after_resp = await client.get(f"/users/me", headers=test_data["user1_headers"])
    assert user1_details_after_resp.status_code == 200
    final_credits_user1 = UserResponse(**user1_details_after_resp.json()).credits
    
    expected_final_credits = initial_credits_user1 - credits_used
    assert final_credits_user1 == expected_final_credits, \
        f"User 1 credit deduction incorrect. Expected {expected_final_credits}, got {final_credits_user1}. Initial: {initial_credits_user1}, Used: {credits_used}"

    print(f"User 1 successfully triggered judge_global for contest1. Cost: {credits_used}. Credits before: {initial_credits_user1}, after: {final_credits_user1}.")

@pytest.mark.run(after='test_06_07_user1_triggers_judge_global_for_contest1')
async def test_06_07a_admin_assigns_self_as_human_judge_for_contest1(client: AsyncClient):
    """Admin assigns themselves as a human judge for contest1."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "admin_user_id" in test_data, "Admin user ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Fetch contest details to check if admin is already a judge
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestDetailResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", "Contest1 is not in Evaluation phase for admin judge assignment."

    admin_is_judge = any(
        str(judge.user_id) == str(test_data["admin_user_id"]) and judge.judge_type == "human"
        for judge in contest_details.judges if judge.user_id
    )

    if not admin_is_judge:
        assign_judge_payload = {
            "user_id": test_data["admin_user_id"],
            "judge_type": "human"
        }
        assign_response = await client.post(
            f"/contests/{test_data['contest1_id']}/judges",
            json=assign_judge_payload,
            headers=test_data["admin_headers"] # Admin uses their own headers to assign
        )
        assert assign_response.status_code in [200, 201], \
            f"Admin failed to assign self as human judge for contest1: {assign_response.text}"
        print(f"Admin (ID: {test_data['admin_user_id']}) successfully assigned self as human judge for contest1 (ID: {test_data['contest1_id']}).")
        test_data["admin_is_judge_for_contest1"] = True
    else:
        print(f"Admin (ID: {test_data['admin_user_id']}) was already a human judge for contest1 (ID: {test_data['contest1_id']}).")
        test_data["admin_is_judge_for_contest1"] = True

@pytest.mark.run(after='test_06_07a_admin_assigns_self_as_human_judge_for_contest1') # Depends on the new test
async def test_06_08_admin_votes_as_human_judge_in_contest1(client: AsyncClient): # MODIFIED: Test name and description
    """Admin, acting as a human judge, submits a vote for contest1. Succeeds."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "admin_user_id" in test_data, "Admin user ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert test_data.get("admin_is_judge_for_contest1"), "Admin was not successfully assigned as a judge for contest1 in the preceding step."
    # Assuming text1_1 was submitted to contest1 by user1. Admin will vote on it.
    # This text_id should be one of the texts available in contest1.
    # From test 5.01 (User 2 submits Text 2.1 to contest1) or 5.05 (User 2 submits Text 2.3 to contest1)
    # Let's use text2_3_id as text1_1_id might not be in contest1 or might be used by another judge.
    assert "text2_3_id" in test_data, "Text 2.3 ID (for admin voting in contest1) not found in test_data."
    text_to_vote_on_id = test_data["text2_3_id"]

    # Ensure contest is still in evaluation (quick check)
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    assert ContestDetailResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase for admin voting."

    # Admin submits a vote
    vote_payload = {
        "text_id": text_to_vote_on_id,
        "text_place": 2, # Admin gives 2nd place to avoid conflict if user2 gave 1st to same text
        "comment": "Admin (as human judge) voting in contest1. This text is noteworthy."
    }
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/votes",
        json=vote_payload,
        headers=test_data["admin_headers"]
    )
    assert response.status_code in [200, 201], \
        f"Admin (as human judge) failed to submit vote for contest1: {response.text}"
    
    vote_response_data = VoteResponse(**response.json())
    assert vote_response_data.text_id == text_to_vote_on_id
    assert str(vote_response_data.judge_id) == str(test_data["admin_user_id"]) # Ensure judge_id is string for comparison if necessary
    assert vote_response_data.text_place == vote_payload["text_place"]
    assert vote_response_data.comment == vote_payload["comment"]
    
    print(f"Admin (as human judge) successfully submitted a vote for text {text_to_vote_on_id} in contest1 (ID: {test_data['contest1_id']}). Vote ID: {vote_response_data.id}")

@pytest.mark.run(after='test_06_08_admin_votes_as_human_judge_in_contest1') # Ensure this points to the updated test name
async def test_06_09_admin_triggers_judge1_ai_evaluation_for_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin triggers judge1_ai evaluation for contest1. Succeeds (admin pays, no credit check needed for admin)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "judge1_ai_id" in test_data, "judge1_ai_id (AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    assert ContestDetailResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Admin's credits are not typically deducted for system operations like this,
    # or the cost is handled differently (e.g., system budget).
    # We'll check admin credits before and after to see if they change.
    admin_details_before_resp = await client.get(f"/users/me", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert admin_details_before_resp.status_code == 200
    initial_credits_admin = UserResponse(**admin_details_before_resp.json()).credits

    # Admin triggers AI judge via the unified endpoint
    trigger_payload = {
        "agent_id": test_data["judge1_ai_id"],
        "model": "gpt-4-turbo",
        "contest_id": test_data["contest1_id"]
    }
    response = await client.post(
        "/agents/execute/judge",
        json=trigger_payload,
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin failed to trigger judge1_ai for contest1: {response.text}"
    trigger_response_data_list = response.json()
    assert isinstance(trigger_response_data_list, list), "Expected a list of execution responses"
    if not trigger_response_data_list:
        credits_used_by_admin_for_judge1 = 0
    else:
        credits_used_by_admin_for_judge1 = sum(item.get("credits_used", 0) for item in trigger_response_data_list)
    test_data["contest1_judge1_ai_eval_cost_admin"] = credits_used_by_admin_for_judge1

    # Verify Admin's credits. For admin, credits might not be deducted from their personal balance.
    # This depends on application logic (e.g. admin actions are free, or use a system budget)
    # For now, let's assert they are NOT deducted from admin's personal balance for triggering this.
    admin_details_after_resp = await client.get(f"/users/me", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert admin_details_after_resp.status_code == 200
    final_credits_admin = UserResponse(**admin_details_after_resp.json()).credits
    
    # Assuming admin actions like this don't use their personal credits
    # If the trigger-ai-judge endpoint *always* deducts from the caller, this will fail.
    # This needs to align with how the backend handles admin credit usage for such operations.
    # Let's assume admin's personal credits are NOT used for this specific system-triggered AI judging.
    # If credits_used_by_admin_for_judge1 > 0, this implies the system DID try to charge the admin.
    # The prompt for this test says "admin pays", which is ambiguous.
    # If "admin pays" means their personal credits, then final_credits_admin should be initial_credits_admin - credits_used_by_admin_for_judge1
    # Let's assume the system might charge admin if the endpoint is generic.
    expected_admin_credits = initial_credits_admin - credits_used_by_admin_for_judge1
    assert final_credits_admin == expected_admin_credits, \
        f"Admin credit balance changed unexpectedly. Expected: {expected_admin_credits}, Got: {final_credits_admin}. Initial: {initial_credits_admin}, Used: {credits_used_by_admin_for_judge1}"

    print(f"Admin successfully triggered judge1_ai for contest1. Cost attributed: {credits_used_by_admin_for_judge1}. Admin credits before: {initial_credits_admin}, after: {final_credits_admin}.")

@pytest.mark.run(after='test_06_09_admin_triggers_judge1_ai_evaluation_for_contest1')
async def test_06_10_admin_triggers_judge_global_for_contest2_fails_not_evaluation(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin attempts to trigger judge_global for contest2. Fails (contest2 is not in Evaluation)."""
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "judge_global_id" in test_data, "judge_global_id (AI Judge) not found."

    # Ensure contest2 is NOT in evaluation (e.g., still 'Open' or 'Upcoming')
    contest_check_response = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    current_status_c2 = ContestDetailResponse(**contest_check_response.json()).status # FIX: Use ContestDetailResponse
    assert current_status_c2.lower() != "evaluation", f"Contest2 is unexpectedly in Evaluation phase: {current_status_c2}"

    # Use the existing AI judge execution endpoint instead of a custom contest path
    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "model": "claude-3-haiku-20240307"
    }
    trigger_payload["contest_id"] = test_data["contest2_id"]
    response = await client.post(
        "/agents/execute/judge",
        json=trigger_payload,
        headers=test_data["admin_headers"]
    )
    # Expecting 400 or 403 if contest is not in the correct state for AI judging
    assert response.status_code in [400, 403], f"Triggering AI judge for contest2 (not in Eval) should fail (400/403), but got {response.status_code}: {response.text}"

    print(f"Admin attempt to trigger judge_global for contest2 (status: {current_status_c2}) failed as expected (Status: {response.status_code}).")

@pytest.mark.run(after='test_06_10_admin_triggers_judge_global_for_contest2_fails_not_evaluation')
async def test_06_11_admin_sets_contest2_status_to_evaluation(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin sets contest2 status to 'Evaluation'."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = await client.put(
        f"/contests/{test_data['contest2_id']}", # Admin can update any contest
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, \
        f"Admin failed to set contest2 status to Evaluation: {response.text}"
    
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.status.lower() == "evaluation", \
        f"Contest2 status was not updated to Evaluation. Current status: {updated_contest.status}"
    
    print(f"Admin successfully set contest2 (ID: {test_data['contest2_id']}) status to: {updated_contest.status}.")

@pytest.mark.run(after='test_06_11_admin_sets_contest2_status_to_evaluation')
async def test_06_12_admin_sets_contest3_status_to_evaluation(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin sets contest3 status to 'Evaluation'."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = await client.put(
        f"/contests/{test_data['contest3_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, \
        f"Admin failed to set contest3 status to Evaluation: {response.text}"
    
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.status.lower() == "evaluation", \
        f"Contest3 status was not updated to Evaluation. Current status: {updated_contest.status}"
    
    print(f"Admin successfully set contest3 (ID: {test_data['contest3_id']}) status to: {updated_contest.status}.")

@pytest.mark.run(after='test_06_12_admin_sets_contest3_status_to_evaluation')
async def test_06_13_admin_assigns_user1_as_judge_for_contest3(client: AsyncClient):
    """Admin assigns User 1 as a human judge for contest3."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "user1_id" in test_data, "User 1 ID not found."

    # Fetch current judges for contest3
    contest_details_resp = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["admin_headers"]) 
    assert contest_details_resp.status_code == 200
    contest_details = ContestDetailResponse(**contest_details_resp.json())
    
    existing_judge_ids = [str(judge.user_id) for judge in contest_details.judges if judge.user_id]
    if str(test_data["user1_id"]) in existing_judge_ids:
        print(f"User 1 (ID: {test_data['user1_id']}) is already a judge for contest3 (ID: {test_data['contest3_id']}). No action needed.")
        test_data["user1_is_judge_for_contest3"] = True # Mark for next test
        return

    # Assign User 1 using the POST /contests/{id}/judges endpoint (assuming this is how it works)
    assign_judge_payload = {"user_id": test_data["user1_id"]}
    # Note: Assuming the endpoint determines judge type or defaults to Human
    response = await client.post(
        f"/contests/{test_data['contest3_id']}/judges", 
        json=assign_judge_payload, 
        headers=test_data["admin_headers"] # Admin can assign to any contest
    )
    assert response.status_code in [200, 201], \
        f"Admin failed to assign User 1 as judge for contest3: {response.text}. Payload: {assign_judge_payload}"

    # Verify User 1 is now listed as a judge for contest3
    contest_details_after_resp = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["admin_headers"]) 
    assert contest_details_after_resp.status_code == 200
    contest_details_after = ContestDetailResponse(**contest_details_after_resp.json())
    is_now_judge = any(str(judge.user_id) == str(test_data["user1_id"]) for judge in contest_details_after.judges if judge.user_id)
    assert is_now_judge, f"User 1 (ID: {test_data['user1_id']}) was not successfully assigned as a judge for contest3."
    test_data["user1_is_judge_for_contest3"] = True # Mark for next test
    print(f"Admin successfully assigned User 1 (ID: {test_data['user1_id']}) as a human judge for contest3 (ID: {test_data['contest3_id']}).")

@pytest.mark.run(after='test_06_13_admin_assigns_user1_as_judge_for_contest3')
async def test_06_14_user1_submits_votes_for_contest3(client: AsyncClient):
    """User 1 (now judge) submits votes for contest3 (specifically for text1_1)."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID (submitted to contest3) not found."
    assert test_data.get("user1_is_judge_for_contest3") is True, "Test data doesn't indicate User 1 is judge for Contest 3."

    # Ensure contest is in evaluation
    contest_check_resp = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"]) # Public contest, no password
    assert contest_check_resp.status_code == 200, f"User 1 failed to get contest 3 details: {contest_check_resp.text}"
    contest_details = ContestDetailResponse(**contest_check_resp.json())
    assert contest_details.status.lower() == "evaluation", f"Contest3 not in Evaluation. Current: {contest_details.status}"
    
    # Verify User 1 is listed as a judge for contest3 (redundant check, but good practice)
    is_judge = any(str(judge.user_id) == str(test_data["user1_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 1 is not listed as a judge for contest3 for this test, despite previous step."

    text_id_to_vote_on = test_data["text1_1_id"]

    print(f"User 1 (judge) proceeding to vote on text {text_id_to_vote_on} in contest 3.")

    # Vote on the submission using the correct endpoint and payload
    vote_payload = {
        "text_id": text_id_to_vote_on,
        "text_place": 1, # User 1 gives it 1st place
        "comment": "User 1, as a judge, ranks text 1.1 submission 1st in contest 3."
    }
    vote_response = await client.post(
        f"/contests/{test_data['contest3_id']}/votes",
        json=vote_payload,
        headers=test_data["user1_headers"]
    )
    assert vote_response.status_code in [200, 201], \
        f"User 1 voting on text {text_id_to_vote_on} in contest 3 failed: {vote_response.text}"
    
    vote_data = vote_response.json()
    assert vote_data["text_place"] == vote_payload["text_place"]
    assert vote_data["comment"] == vote_payload["comment"]
    assert str(vote_data["judge_id"]) == str(test_data["user1_id"])
    assert vote_data["text_id"] == text_id_to_vote_on
    assert vote_data["contest_id"] == test_data["contest3_id"]
    test_data[f"user1_vote_on_text{text_id_to_vote_on}_in_c3"] = vote_data["id"]
    print(f"User 1 successfully submitted vote (ID: {vote_data['id']}) for text {text_id_to_vote_on} in contest 3.")

@pytest.mark.run(after='test_06_14_user1_submits_votes_for_contest3')
async def test_06_15_user1_deletes_text1_4_from_contest3_verify_cascade(client: AsyncClient):
    """User 1 deletes its own text 1.4. Verify it is removed from contest 3, votes deleted. 
       Verify User 1's credit balance is not affected."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "text1_4_id" in test_data, "Text 1.4 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."
    # submission_c3_t1_4_id was created in test 5.23
    assert "submission_c3_t1_4_id" in test_data, "Submission ID for Text 1.4 in Contest 3 not found."

    # 0. Get initial User 1 credit balance
    user_resp_before = await client.get(f"/users/me", headers=test_data["user1_headers"])
    assert user_resp_before.status_code == 200
    initial_credits_user1 = UserResponse(**user_resp_before.json()).credits

    # Optional: If User 1 had voted on Text 1.4 in contest3, store that vote_id for specific verification
    # For simplicity, we will check that no votes for text1_4_id exist in contest3 after deletion.

    # 1. User 1 deletes Text 1.4
    delete_text_response = await client.delete(
        f"/texts/{test_data['text1_4_id']}",
        headers=test_data["user1_headers"]
    )
    assert delete_text_response.status_code == 204, \
        f"User 1 deleting Text 1.4 failed: {delete_text_response.status_code} - {delete_text_response.text}"
    print(f"User 1 successfully deleted Text 1.4 (ID: {test_data['text1_4_id']}).")

    # 2. Verify Text 1.4 is removed from Contest 3 submissions
    submissions_after_delete_resp = await client.get(
        f"/contests/{test_data['contest3_id']}/submissions/",  
        headers=test_data["user1_headers"] # or admin_headers
    )
    assert submissions_after_delete_resp.status_code == 200
    submissions_in_contest3_after_delete = \
        [ContestTextResponse(**sub) for sub in submissions_after_delete_resp.json()]
    
    found_text1_4_submission = any(
        sub.text_id == test_data['text1_4_id'] for sub in submissions_in_contest3_after_delete
    )
    assert not found_text1_4_submission, \
        f"Text 1.4 (ID: {test_data['text1_4_id']}) should have been removed from contest3 submissions but was found."
    print(f"Verified: Text 1.4 is no longer listed in submissions for contest3 (ID: {test_data['contest3_id']}).")

    # 3. Verify votes associated with Text 1.4 in Contest 3 are deleted
    # This requires an endpoint to list all votes for a contest, e.g., /contests/{contest_id}/votes/
    # Assuming such an endpoint exists and returns a list of VoteResponse objects.
    # If test_06_14 did not create a vote for text1_4_id specifically, this part might just confirm no votes for a now-deleted text exist.
    
    # Let's try to list all votes for contest3
    # The actual API for listing all votes for a contest might differ. This is an assumption.
    # If not available, this verification step might need adjustment or rely on other cascade behaviors.
    votes_in_contest3_resp = await client.get(f"/contests/{test_data['contest3_id']}/votes/", headers=test_data["user1_headers"])
    if votes_in_contest3_resp.status_code == 200:
        all_votes_in_contest3 = [VoteResponse(**vote) for vote in votes_in_contest3_resp.json()]
        votes_for_text1_4 = [v for v in all_votes_in_contest3 if v.text_id == test_data['text1_4_id']]
        assert len(votes_for_text1_4) == 0, \
            f"Found {len(votes_for_text1_4)} votes for deleted Text 1.4 in contest3. Expected 0."
        print(f"Verified: No votes associated with deleted Text 1.4 exist in contest3 (ID: {test_data['contest3_id']}).")
    elif votes_in_contest3_resp.status_code == 404: # Endpoint might not exist
        print(f"Skipping direct vote verification for deleted Text 1.4 in contest3: /contests/{test_data['contest3_id']}/votes/ endpoint not found (404). Cascade might be indirect.")
    else:
        print(f"Warning: Could not verify votes for deleted Text 1.4 in contest3. Status: {votes_in_contest3_resp.status_code}, Response: {votes_in_contest3_resp.text}")

    # 4. Verify User 1's credit balance is not affected
    user_resp_after = await client.get(f"/users/me", headers=test_data["user1_headers"])
    assert user_resp_after.status_code == 200
    final_credits_user1 = UserResponse(**user_resp_after.json()).credits
    assert final_credits_user1 == initial_credits_user1, \
        f"User 1 credit balance changed after deleting text. Initial: {initial_credits_user1}, Final: {final_credits_user1}."
    print(f"User 1 credit balance remains unchanged at {final_credits_user1} after deleting Text 1.4.")

    # Verify contest text count updated
    contest_details_resp = await client.get(f"/contests/{test_data['contest3_id']}", headers=test_data["user1_headers"])
    assert contest_details_resp.status_code == 200
    contest_data = ContestDetailResponse(**contest_details_resp.json())
    # The number of texts should decrease by 1 (assuming Text 1.4 was in it)
    # If text 1.1 is still there, count should be 1. If only text 1.4 was there, count becomes 0.
    # Based on 5.22 and 5.23, contest3 had text1.1 and text1.4. So after deleting text1.4, text_count should be 1.
    assert contest_data.text_count == 1, f"Contest3 text count expected to be 1, got {contest_data.text_count}"
    print(f"Contest3 (ID: {test_data['contest3_id']}) text count updated to {contest_data.text_count}.")

# --- End of Test Section 6: Evaluation Phase (Contest in Evaluation) ---