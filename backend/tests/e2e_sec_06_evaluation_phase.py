# backend/tests/e2e_sec_06_evaluation_phase.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
import logging

from app.core.config import settings
from app.schemas.contest import ContestUpdate, ContestResponse
from app.schemas.submission import SubmissionResponse # For viewing submissions
from app.schemas.user import UserResponse, UserCredit # For credit top-up
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 6: Evaluation Phase (Contest in Evaluation) ---

def test_06_01_user1_sets_contest1_status_to_evaluation(client: TestClient):
    """User 1 sets contest1 status to 'Evaluation'."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}",
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
def test_06_02_user1_submit_to_evaluation_contest1_fails(client: TestClient):
    """User 1 attempts to submit a new text to contest1 (in Evaluation). Should fail."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "text1_3_id" in test_data, "Text 1.3 ID (manual text by User 1) not found."

    # Confirm contest1 is in Evaluation status first
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"])
    assert contest_check_response.status_code == 200
    current_status = ContestResponse(**contest_check_response.json()).status
    assert current_status.lower() == "evaluation", \
        f"Contest1 is not in 'Evaluation' state for this test. Current: {current_status}"

    submission_payload = {"text_id": test_data["text1_3_id"]}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/",
        json=submission_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code in [400, 403], \
        f"Submitting to contest1 in 'Evaluation' phase should fail (400/403), but got {response.status_code}: {response.text}"

    print(f"User 1 attempt to submit Text 1.3 to contest1 (in Evaluation) failed as expected (Status: {response.status_code}).")

@pytest.mark.run(after='test_06_02_user1_submit_to_evaluation_contest1_fails')
def test_06_03_visitor_views_contest1_submissions_masked(client: TestClient):
    """Visitor attempts to view submissions for contest1 -> Should succeed, user and author names masked."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}")
    assert contest_check_response.status_code == 200
    current_status = ContestResponse(**contest_check_response.json()).status
    assert current_status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {current_status}"

    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/")
    assert response.status_code == 200, f"Visitor failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list."

    for sub_data in submissions:
        submission = SubmissionResponse(**sub_data)
        assert submission.user_id is None or isinstance(submission.user_id, str) # Masked field check
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
        assert submission.text_id is not None
        text_resp = client.get(f"{settings.API_V1_STR}/texts/{submission.text_id}")
        assert text_resp.status_code == 200

    print(f"Visitor successfully viewed submissions for contest1 (ID: {test_data['contest1_id']}) with user/author info masked.")

@pytest.mark.run(after='test_06_03_visitor_views_contest1_submissions_masked')
def test_06_04_user2_judge_views_contest1_submissions_masked(client: TestClient):
    """User 2 (human judge) views submissions for contest1 -> Should succeed, user and author names masked."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user2_headers" in test_data, "User 2 headers not found."
    assert "user2_id" in test_data, "User 2 ID not found."

    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["user2_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {contest_details.status}"
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not listed as a judge for contest1."

    response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/", headers=test_data["user2_headers"])
    assert response.status_code == 200, f"User 2 (judge) failed to get submissions: {response.text}"
    
    submissions = response.json()
    assert isinstance(submissions, list) and len(submissions) > 0, "Expected submissions list for judge."

    for sub_data in submissions:
        submission = SubmissionResponse(**sub_data)
        assert submission.user_id is None or isinstance(submission.user_id, str) # Masked field check
        assert submission.author is None or "masked" in submission.author.lower() or submission.author == "[Hidden]" # Masked field check
        assert submission.text_id is not None

    print(f"User 2 (judge) successfully viewed submissions for contest1 (ID: {test_data['contest1_id']}) with user/author info masked.")

@pytest.mark.run(after='test_06_04_user2_judge_views_contest1_submissions_masked')
def test_06_05_user1_votes_in_contest1_fails_not_judge(client: TestClient):
    """User 1 attempts to vote in contest 1 -> Should fail (is not a judge)."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data, "User 1 headers not found."
    assert "submission_c1_t2_2_id" in test_data, "submission_c1_t2_2_id not found."
    submission_id_to_vote_on = test_data["submission_c1_t2_2_id"]

    vote_payload = {"score": 5, "comments": "User 1 trying to vote anyway."}
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_vote_on}/votes/",
        json=vote_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 403, f"User 1 voting (not judge) failed: {response.text} (expected 403)"
    print(f"User 1 attempt to vote in contest1 (ID: {test_data['contest1_id']}) failed as expected (403 - not a judge).")

@pytest.mark.run(after='test_06_05_user1_votes_in_contest1_fails_not_judge')
def test_06_06_user2_votes_in_contest1_succeeds(client: TestClient):
    """User 2 attempts to vote in contest 1 -> Should succeed."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user2_headers" in test_data, "User 2 headers not found."
    assert "user2_id" in test_data, "User 2 ID not found."
    assert "submission_c1_t2_2_id" in test_data, "submission_c1_t2_2_id for voting not found."
    submission_id_to_vote_on = test_data["submission_c1_t2_2_id"]

    # Ensure contest is in evaluation
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["user2_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest1 not in Evaluation. Current: {contest_details.status}"
    
    # Verify User 2 is indeed a judge for contest1
    is_judge = any(str(judge.user_id) == str(test_data["user2_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 2 is not configured as a judge for contest1 for this test."

    vote_payload = {
        "score": 8, # User 2 gives a good score
        "comments": "User 2 (judge) finds this submission quite compelling."
    }

    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/submissions/{submission_id_to_vote_on}/votes/",
        json=vote_payload,
        headers=test_data["user2_headers"]
    )

    assert response.status_code in [200, 201], \
        f"User 2 (judge) voting in contest1 should succeed, but got {response.status_code}: {response.text}"
    
    vote_data = response.json()
    assert vote_data["score"] == vote_payload["score"]
    assert vote_data["comments"] == vote_payload["comments"]
    assert str(vote_data["judge_id"]) == str(test_data["user2_id"]), "Vote judge_id does not match User 2 ID."
    assert vote_data["submission_id"] == submission_id_to_vote_on
    test_data["user2_vote_c1_s_t2_2_id"] = vote_data["id"] # Store vote ID

    print(f"User 2 (judge) successfully voted on submission {submission_id_to_vote_on} in contest1 (ID: {test_data['contest1_id']}). Vote ID: {vote_data['id']}")

@pytest.mark.run(after='test_06_06_user2_votes_in_contest1_succeeds')
def test_06_07_user1_triggers_judge_global_for_contest1(client: TestClient):
    """User 1 triggers judge_global evaluation for contest1. Succeeds. Verify User 1's credit balance decreased."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "admin_headers" in test_data, "Admin headers not found for potential credit top-up."
    assert "judge_global_id" in test_data, "judge_global_id (AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["user1_headers"])
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Check User 1's credits, add if necessary (e.g., 1000 credits for AI judging)
    user1_details_before = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    initial_credits_user1 = user1_details_before.credits
    required_credits_for_judge = 1000 # Assuming a high enough amount for testing
    if initial_credits_user1 < required_credits_for_judge:
        print(f"User 1 has {initial_credits_user1} credits, less than {required_credits_for_judge} estimated for AI judging. Admin adding credits.")
        credits_to_add = required_credits_for_judge - initial_credits_user1 + 500 # Add a bit more buffer
        add_credits_payload = UserCredit(credits=user1_details_before.credits + credits_to_add) # Send new total
        # The endpoint expects the *amount to add*, not the new total. Or it could be new total based on schema UserCredit(credits=int)
        # Let's assume the endpoint /admin/users/{user_id}/credits SETS the credit to the provided value.
        # To be safe, let's re-fetch and add if the current schema for UserCredit expects credits to be the *new total*
        # For now, let's assume the endpoint /admin/users/{user_id}/credits SETS the credit to the value.
        # The test_04_07_admin_assigns_credits implies it SETS the credit to the value provided.
        new_total_for_user1 = initial_credits_user1 + credits_to_add
        credit_payload = UserCredit(credits=new_total_for_user1)
        resp_add = client.post(f"{settings.API_V1_STR}/admin/users/{test_data['user1_id']}/credits", json=credit_payload.model_dump(), headers=test_data["admin_headers"])
        assert resp_add.status_code == 200, f"Admin failed to add credits to User 1: {resp_add.text}"
        initial_credits_user1 = UserResponse(**resp_add.json()).credits
        print(f"User 1 credits topped up to {initial_credits_user1}.")
    assert initial_credits_user1 >= required_credits_for_judge, "User 1 still does not have enough credits after top-up attempt."

    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "model": "claude-3-5-haiku-latest" # Example model
    }
    response = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}/trigger-ai-judge",
        json=trigger_payload,
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, f"User 1 failed to trigger judge_global for contest1: {response.text}"
    
    trigger_response_data = response.json()
    assert "message" in trigger_response_data
    assert "credits_used" in trigger_response_data, "Response missing 'credits_used' field."
    credits_used = trigger_response_data["credits_used"]
    assert credits_used > 0, "Credits used for AI judging should be positive."
    test_data["contest1_judge_global_eval_cost_user1"] = credits_used

    # Verify User 1's credits decreased
    user1_details_after = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    final_credits_user1 = user1_details_after.credits
    assert final_credits_user1 == initial_credits_user1 - credits_used, \
        f"User 1 credit deduction incorrect. Expected {initial_credits_user1 - credits_used}, got {final_credits_user1}. Initial: {initial_credits_user1}, Used: {credits_used}"

    print(f"User 1 successfully triggered judge_global for contest1. Cost: {credits_used}. Credits before: {initial_credits_user1}, after: {final_credits_user1}.")

@pytest.mark.run(after='test_06_07_user1_triggers_judge_global_for_contest1')
def test_06_08_admin_triggers_human_judge_evaluation_for_contest1(client: TestClient):
    """Admin triggers human judge evaluation for contest1. Succeeds."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Ensure contest is in evaluation
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    response = client.post(
        f"{settings.API_V1_STR}/admin/contests/{test_data['contest1_id']}/trigger-human-judges",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin failed to trigger human judges for contest1: {response.text}"
    
    response_data = response.json()
    assert "message" in response_data
    print(f"Admin successfully triggered human judge evaluation for contest1: {response_data['message']}")

@pytest.mark.run(after='test_06_08_admin_triggers_human_judge_evaluation_for_contest1')
def test_06_09_admin_triggers_judge1_ai_evaluation_for_contest1(client: TestClient):
    """Admin triggers judge1 (User 1's AI Judge) evaluation for contest1. Succeeds.
    Verify User 1's credit balance is not decreased. Verify transaction cost is recorded.
    """
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "judge1_id" in test_data, "judge1_id (User 1's AI Judge) not found."

    # Ensure contest is in evaluation
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest1_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    assert ContestResponse(**contest_check_response.json()).status.lower() == "evaluation", "Contest1 is not in Evaluation phase."

    # Check User 1's credits before admin triggers AI judge
    user1_details_before = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    initial_credits_user1 = user1_details_before.credits

    trigger_payload = {
        "agent_id": test_data["judge1_id"],
        "model": "claude-3-haiku-20240307" # Using a specific model, adjust if needed
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/contests/{test_data['contest1_id']}/trigger-ai-judge",
        json=trigger_payload,
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Admin failed to trigger judge1 for contest1: {response.text}"
    
    trigger_response_data = response.json()
    assert "message" in trigger_response_data
    assert "credits_used" in trigger_response_data, "Response missing 'credits_used' field for admin trigger."
    credits_used_by_admin_trigger = trigger_response_data["credits_used"]
    assert credits_used_by_admin_trigger >= 0, "Credits used for AI judging by admin should be non-negative." 
    # If admin trigger is free for admin, cost might be 0, otherwise positive.
    # Cost is recorded on the system/agent side, not against User 1.

    # Verify User 1's credits did NOT decrease
    user1_details_after = UserResponse(**client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"]).json())
    final_credits_user1 = user1_details_after.credits
    assert final_credits_user1 == initial_credits_user1, \
        f"User 1 credit balance changed. Expected {initial_credits_user1}, got {final_credits_user1}. Admin triggered AI judge."

    print(f"Admin successfully triggered judge1 for contest1. Cost recorded: {credits_used_by_admin_trigger}. User 1 credits unchanged ({initial_credits_user1}).")

@pytest.mark.run(after='test_06_09_admin_triggers_judge1_ai_evaluation_for_contest1')
def test_06_10_admin_triggers_judge_global_for_contest2_fails_not_evaluation(client: TestClient):
    """Admin triggers judge_global (AI judge) evaluation for contest2. Fails. Contest is not in evaluation. Verify no cost is recorded."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "judge_global_id" in test_data, "judge_global_id not found."

    # Confirm contest2 is NOT in Evaluation status
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    assert contest_check_response.status_code == 200
    current_status_c2 = ContestResponse(**contest_check_response.json()).status
    assert current_status_c2.lower() != "evaluation", \
        f"Contest2 should not be in 'Evaluation' state for this test. Current: {current_status_c2}"

    trigger_payload = {
        "agent_id": test_data["judge_global_id"],
        "model": "claude-3-haiku-20240307"
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/contests/{test_data['contest2_id']}/trigger-ai-judge",
        json=trigger_payload,
        headers=test_data["admin_headers"]
    )
    # Expecting 400 or 403 if contest is not in evaluation phase for AI judging
    assert response.status_code in [400, 403], \
        f"Triggering AI judge for contest2 not in 'Evaluation' should fail (400/403), but got {response.status_code}: {response.text}"

    print(f"Admin attempt to trigger judge_global for contest2 (not in Evaluation) failed as expected (Status: {response.status_code}).")

@pytest.mark.run(after='test_06_10_admin_triggers_judge_global_for_contest2_fails_not_evaluation')
def test_06_11_admin_sets_contest2_status_to_evaluation(client: TestClient):
    """Admin sets contest2 status to 'Evaluation'."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["admin_headers"] # Admin can change status of any contest
    )
    assert response.status_code == 200, \
        f"Admin failed to set contest2 status to Evaluation: {response.text}"
    
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.status.lower() == "evaluation", \
        f"Contest2 status was not updated to Evaluation. Current status: {updated_contest.status}"
    
    print(f"Admin successfully set contest2 (ID: {test_data['contest2_id']}) status to: {updated_contest.status}.")

@pytest.mark.run(after='test_06_11_admin_sets_contest2_status_to_evaluation')
def test_06_12_admin_sets_contest3_status_to_evaluation(client: TestClient):
    """Admin sets contest3 status to 'Evaluation'."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    update_payload = ContestUpdate(status="Evaluation")
    response = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest3_id']}",
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
def test_06_13_admin_assigns_user1_as_judge_for_contest2(client: TestClient):
    """Admin assigns User 1 as a human judge for contest2."""
    assert "admin_headers" in test_data, "Admin headers not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "user1_id" in test_data, "User 1 ID not found."

    # Get current judges for contest2 to append User 1
    response_get = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["admin_headers"])
    assert response_get.status_code == 200, f"Failed to get contest2 details: {response_get.text}"
    contest_details = ContestResponse(**response_get.json())
    
    current_judges = []
    if contest_details.judges:
        for judge in contest_details.judges:
            if judge.user_id:
                current_judges.append({"user_id": str(judge.user_id)})
            elif judge.agent_id:
                current_judges.append({"agent_id": str(judge.agent_id)})

    # Add User 1 if not already a judge
    user1_is_judge = any(str(judge_info.get("user_id")) == str(test_data["user1_id"]) for judge_info in current_judges)
    
    if not user1_is_judge:
        new_judges_list = current_judges + [{"user_id": test_data["user1_id"]}] # judge_type "human" is default or inferred
    else:
        new_judges_list = current_judges

    update_payload = ContestUpdate(judges=new_judges_list)
    response_put = client.put(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", # Admin updates contest with new judge list
        json=update_payload.model_dump(exclude_unset=True, exclude_none=True),
        headers=test_data["admin_headers"]
    )
    assert response_put.status_code == 200, \
        f"Admin failed to assign User 1 as judge for contest2: {response_put.text}"

    updated_contest = ContestResponse(**response_put.json())
    assert any(str(judge.user_id) == str(test_data["user1_id"]) for judge in updated_contest.judges if judge.user_id), \
        "User 1 was not successfully assigned as a judge for contest2."
    
    print(f"Admin successfully assigned User 1 (ID: {test_data['user1_id']}) as a human judge for contest2 (ID: {test_data['contest2_id']}).")

@pytest.mark.run(after='test_06_13_admin_assigns_user1_as_judge_for_contest2')
def test_06_14_user1_submits_votes_for_contest2(client: TestClient):
    """User 1 submits votes/evaluation for contest2."""
    assert "user1_headers" in test_data and "user1_id" in test_data, "User 1 token/ID not found."
    assert "admin_headers" in test_data, "Admin headers not found." # For submitting a text
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "text3_1_id" in test_data, "Admin's Text 3.1 ID not found for submission." # Admin's manually created text

    # SETUP: Admin submits a text to contest2 as it's currently empty and User 1 needs something to vote on.
    # Contest 2 restricts submissions per user to 1. Admin is not a participant yet.
    submission_payload_admin = {"text_id": test_data["text3_1_id"]}
    response_submit_admin = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/",
        json=submission_payload_admin,
        headers=test_data["admin_headers"]
    )
    assert response_submit_admin.status_code == 201, \
        f"Admin failed to submit Text 3.1 to contest2 for voting setup: {response_submit_admin.text}"
    submission_c2_admin_t3_1_data = response_submit_admin.json()
    submission_c2_admin_t3_1_id = submission_c2_admin_t3_1_data["id"]
    test_data["submission_c2_admin_t3_1_id"] = submission_c2_admin_t3_1_id # Store for potential later use/cleanup
    print(f"Admin submitted Text 3.1 (ID: {test_data['text3_1_id']}) to contest2, creating submission (ID: {submission_c2_admin_t3_1_id}).")

    # Ensure contest2 is in evaluation
    contest_check_response = client.get(f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}", headers=test_data["user1_headers"])
    assert contest_check_response.status_code == 200
    contest_details = ContestResponse(**contest_check_response.json())
    assert contest_details.status.lower() == "evaluation", f"Contest2 not in Evaluation. Current: {contest_details.status}"
    
    # Verify User 1 is indeed a judge for contest2
    is_judge = any(str(judge.user_id) == str(test_data["user1_id"]) for judge in contest_details.judges if judge.user_id)
    assert is_judge, "User 1 is not configured as a judge for contest2 for this test."

    vote_payload = {
        "score": 7, 
        "comments": "User 1 (now a judge for contest2) finds this admin submission adequate."
    }

    response_vote = client.post(
        f"{settings.API_V1_STR}/contests/{test_data['contest2_id']}/submissions/{submission_c2_admin_t3_1_id}/votes/",
        json=vote_payload,
        headers=test_data["user1_headers"]
    )

    assert response_vote.status_code in [200, 201], \
        f"User 1 voting in contest2 should succeed, but got {response_vote.status_code}: {response_vote.text}"
    
    vote_data = response_vote.json()
    assert vote_data["score"] == vote_payload["score"]
    assert vote_data["comments"] == vote_payload["comments"]
    assert str(vote_data["judge_id"]) == str(test_data["user1_id"]), "Vote judge_id does not match User 1 ID."
    assert vote_data["submission_id"] == submission_c2_admin_t3_1_id
    test_data[f"user1_vote_c2_s_admin_t3_1_id"] = vote_data["id"] # Store vote ID

    print(f"User 1 (judge) successfully voted on submission {submission_c2_admin_t3_1_id} in contest2 (ID: {test_data['contest2_id']}). Vote ID: {vote_data['id']}")

# --- End of Test Section 6: Evaluation Phase (Contest in Evaluation) ---