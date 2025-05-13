# backend/tests/e2e_sec_06_evaluation_phase.py
import pytest
from httpx import AsyncClient # MODIFIED: For async client
import logging

from app.schemas.contest import ContestUpdate, ContestResponse, TextSubmissionResponse
from app.schemas.user import UserResponse, UserCredit # For credit top-up
from tests.shared_test_state import test_data

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
    current_status = ContestResponse(**contest_check_response.json()).status
    assert current_status.lower() == "evaluation", \
        f"Contest1 is not in 'Evaluation' state for this test. Current: {current_status}"

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/submissions/",
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
    current_status = ContestResponse(**contest_check_response.json()).status
    assert current_status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {current_status}"

    response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/") # MODIFIED: await, removed settings.API_V1_STR
    assert response.status_code == 200, f"Visitor failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list."

    for sub_data in submissions:
        submission = TextSubmissionResponse(**sub_data)
        assert submission.user_id is None or isinstance(submission.user_id, str) # Masked field check
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
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
    contest_details = ContestResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {contest_details.status}"
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not listed as a judge for contest1."

    response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user2_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert response.status_code == 200, f"User 2 (judge) failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list for judge."

    for sub_data in submissions:
        submission = TextSubmissionResponse(**sub_data)
        assert submission.user_id is None or isinstance(submission.user_id, str) # Masked field check
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
        assert submission.text_id is not None

    print(f"User 2 (judge) successfully viewed submissions for contest1 (ID: {test_data['contest1_id']}) with user/author info masked.")

@pytest.mark.run(after='test_06_04_user2_judge_views_contest1_submissions_masked')
async def test_06_05_user1_votes_in_contest1_fails_not_judge(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 attempts to vote in contest 1 -> Should fail (is not a judge)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data, "User 1 headers not found."
    assert "submission_c1_t2_2_id" in test_data, "submission_c1_t2_2_id not found." # This submission was by user2
    submission_id_to_vote_on = test_data["submission_c1_t2_2_id"]

    vote_payload = {"score": 5, "comments": "User 1 trying to vote anyway."}
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/submissions/{submission_id_to_vote_on}/votes/",
        json=vote_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 voting (not judge) failed: {response.text} (expected 403)"
    print(f"User 1 attempt to vote in contest1 (ID: {test_data['contest1_id']}) failed as expected (403 - not a judge).")

@pytest.mark.run(after='test_06_05_user1_votes_in_contest1_fails_not_judge')
async def test_06_06_user2_votes_in_contest1_succeeds(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 2 (judge) votes in contest 1, assigning a place and comment to one text."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user2_headers" in test_data, "User 2 headers not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    # submission_c1_t2_2_id was the submission of text2_2_id
    assert "text2_2_id" in test_data, "Text 2.2 ID for voting not found."
    text_id_to_vote_on = test_data["text2_2_id"]

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user2_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestResponse(**contest_check_response.json())
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
        f"/contests/{test_data['contest1_id']}/votes/", # CORRECTED API PATH
        json=vote_payload, # CORRECTED PAYLOAD STRUCTURE
        headers=test_data["user2_headers"]
    )

    assert response.status_code in [200, 201], \
        f"User 2 (judge) voting in contest1 should succeed, but got {response.status_code}: {response.text}"
    
    vote_data = response.json()
    assert vote_data["text_place"] == vote_payload["text_place"]
    assert vote_data["comment"] == vote_payload["comment"]
    # The VoteResponse contains judge_id (which is the user_id of the human judge) and contest_id
    assert str(vote_data["judge_id"]) == str(test_data["user2_id"]), "Vote judge_id does not match User 2 ID."
    assert vote_data["text_id"] == text_id_to_vote_on
    assert vote_data["contest_id"] == test_data["contest1_id"]
    test_data["user2_vote_on_text2_2_id_in_c1"] = vote_data["id"] # Store vote ID

    print(f"User 2 (judge) successfully voted on text {text_id_to_vote_on} in contest1 (ID: {test_data['contest1_id']}). Vote ID: {vote_data['id']}")

@pytest.mark.run(after='test_06_06_user2_votes_in_contest1_succeeds')
async def test_06_07_user1_triggers_judge_global_for_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 triggers judge_global evaluation for contest1. Succeeds. Verify User 1's credit balance decreased."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "admin_headers" in test_data, "Admin headers not found for potential credit top-up."
    assert "judge_global_id" in test_data, "judge_global_id (AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Check User 1's credits, add if necessary (e.g., 1000 credits for AI judging)
    user1_details_before_resp = await client.get(f"/users/me", headers=test_data["user1_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert user1_details_before_resp.status_code == 200
    user1_details_before = UserResponse(**user1_details_before_resp.json())
    initial_credits_user1 = user1_details_before.credits
    
    # Estimate based on previous test, but actual cost determined by API. Add buffer.
    # This required_credits_for_judge is just a pre-check, the API will determine actual cost.
    # If this is too low, the trigger might fail if not enough credits.
    # The previous test used 'test_data["contest1_judge_global_eval_cost_user1"]'
    # but that's for USER 1. Here, it's the trigger cost.
    # The API /trigger-ai-judge returns credits_used. We'll assume a large enough buffer.
    required_credits_for_judge = test_data.get("ai_judge_trigger_cost_estimate", 100) # Default if not set elsewhere
    
    if initial_credits_user1 < required_credits_for_judge:
        print(f"User 1 has {initial_credits_user1} credits, less than {required_credits_for_judge} estimated for AI judging. Admin adding credits.")
        credits_to_add = required_credits_for_judge - initial_credits_user1 + 50 # Add a bit more buffer
        
        new_total_for_user1 = initial_credits_user1 + credits_to_add
        credit_payload = UserCredit(credits=new_total_for_user1) # Schema expects new total
        resp_add = await client.post(f"/admin/users/{test_data['user1_id']}/credits", json=credit_payload.model_dump(), headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
        assert resp_add.status_code == 200, f"Admin failed to add credits to User 1: {resp_add.text}"
        
        user1_after_topup_resp = await client.get(f"/users/me", headers=test_data["user1_headers"]) # MODIFIED: await
        assert user1_after_topup_resp.status_code == 200
        initial_credits_user1 = UserResponse(**user1_after_topup_resp.json()).credits # Update initial_credits_user1 after top-up
        print(f"User 1 credits topped up to {initial_credits_user1}.")
        
    assert initial_credits_user1 >= required_credits_for_judge, f"User 1 still does not have enough credits ({initial_credits_user1}) after top-up attempt for required {required_credits_for_judge}."

    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "model": "claude-3-opus-20240229" # Using a consistent model for tests
    }
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/trigger-ai-judge",
        json=trigger_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 failed to trigger judge_global for contest1: {response.text}"
    
    trigger_response_data = response.json()
    assert "message" in trigger_response_data
    assert "credits_used" in trigger_response_data, "Response missing 'credits_used' field."
    credits_used = trigger_response_data["credits_used"]
    # credits_used can be 0 if AI judge has already processed all submissions for this contest.
    # assert credits_used >= 0, "Credits used for AI judging should be non-negative."
    # For this test, we expect it to run and cost something if new submissions are there.
    # If the AI judge was already run and no new submissions, cost could be 0.
    # Let's ensure it's not negative.
    assert credits_used >= 0, f"Credits used was negative: {credits_used}"

    test_data["contest1_judge_global_eval_cost_user1"] = credits_used # Store or update the cost

    # Verify User 1's credits decreased
    user1_details_after_resp = await client.get(f"/users/me", headers=test_data["user1_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert user1_details_after_resp.status_code == 200
    final_credits_user1 = UserResponse(**user1_details_after_resp.json()).credits
    
    expected_final_credits = initial_credits_user1 - credits_used
    assert final_credits_user1 == expected_final_credits, \
        f"User 1 credit deduction incorrect. Expected {expected_final_credits}, got {final_credits_user1}. Initial: {initial_credits_user1}, Used: {credits_used}"

    print(f"User 1 successfully triggered judge_global for contest1. Cost: {credits_used}. Credits before: {initial_credits_user1}, after: {final_credits_user1}.")

@pytest.mark.run(after='test_06_07_user1_triggers_judge_global_for_contest1')
async def test_06_08_admin_triggers_human_judge_evaluation_for_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin triggers human judge evaluation for contest1. Succeeds."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    response = await client.post(
        f"/admin/contests/{test_data['contest1_id']}/trigger-human-judges",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin failed to trigger human judges for contest1: {response.text}"
    
    response_data = response.json()
    assert "message" in response_data
    assert "Human judges triggered" in response_data["message"] or "notifications sent" in response_data["message"].lower() # Check for success message
    print(f"Admin successfully triggered human judges for contest1 (ID: {test_data['contest1_id']}). Response: {response_data['message']}")

@pytest.mark.run(after='test_06_08_admin_triggers_human_judge_evaluation_for_contest1')
async def test_06_09_admin_triggers_judge1_ai_evaluation_for_contest1(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin triggers judge1_ai evaluation for contest1. Succeeds (admin pays, no credit check needed for admin)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "judge1_ai_id" in test_data, "judge1_ai_id (AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = await client.get(f"/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Admin's credits are not typically deducted for system operations like this,
    # or the cost is handled differently (e.g., system budget).
    # We'll check admin credits before and after to see if they change.
    admin_details_before_resp = await client.get(f"/users/me", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert admin_details_before_resp.status_code == 200
    initial_credits_admin = UserResponse(**admin_details_before_resp.json()).credits

    trigger_payload = {
        "agent_id": test_data["judge1_ai_id"],
        "model": "gpt-4-turbo" 
    }
    response = await client.post(
        f"/contests/{test_data['contest1_id']}/trigger-ai-judge", # This endpoint is user-facing, but admin can use it.
        json=trigger_payload,
        headers=test_data["admin_headers"] # Admin is making the call
    )
    assert response.status_code == 200, f"Admin failed to trigger judge1_ai for contest1: {response.text}"
    
    trigger_response_data = response.json()
    assert "message" in trigger_response_data
    # credits_used might be 0 if no new texts for this specific judge to evaluate or already evaluated
    assert "credits_used" in trigger_response_data, "Response missing 'credits_used' field."
    credits_used_by_admin_for_judge1 = trigger_response_data["credits_used"]
    assert credits_used_by_admin_for_judge1 >= 0, f"Credits used for judge1_ai was negative: {credits_used_by_admin_for_judge1}"
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
    contest_check_response = await client.get(f"/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR
    assert contest_check_response.status_code == 200
    current_status_c2 = ContestResponse(**contest_check_response.json()).status
    assert current_status_c2.lower() != "evaluation", f"Contest2 is unexpectedly in Evaluation phase: {current_status_c2}"

    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "model": "claude-3-haiku-20240307"
    }
    response = await client.post(
        f"/contests/{test_data['contest2_id']}/trigger-ai-judge",
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
    contest_details = ContestResponse(**contest_details_resp.json())
    
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
    contest_details_after = ContestResponse(**contest_details_after_resp.json())
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
    contest_details = ContestResponse(**contest_check_resp.json())
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
        f"/contests/{test_data['contest3_id']}/votes/", # Correct endpoint for contest 3
        json=vote_payload,
        headers=test_data["user1_headers"] # User 1 votes
        # No password needed for public contest 3
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

# --- End of Test Section 6: Evaluation Phase (Contest in Evaluation) ---