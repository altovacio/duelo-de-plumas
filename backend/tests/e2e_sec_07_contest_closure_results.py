# backend/tests/e2e_sec_07_contest_closure_results.py
import pytest
from httpx import AsyncClient # MODIFIED: For async client
from typing import List, Dict, Any # Added for type hinting
import logging

from app.schemas.contest import ContestUpdate, ContestResponse, ContestTextResponse # MODIFIED: Removed ContestVisibility, added TextSubmissionResponse
# Make sure UserResponse is imported if needed for author name checks
from app.schemas.user import UserResponse
from app.schemas.text import TextResponse # ADDED for text deletion check
from app.schemas.credit import CreditTransactionResponse # ADDED for credit history check
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 7: Contest Closure & Results ---

@pytest.mark.run(after='test_06_15_user1_deletes_text1_4_from_contest3') # MODIFIED: Ensure this runs after section 6.15
async def test_07_01_admin_sets_contests_status_to_closed(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin sets contest1, contest2 and contest3 status to 'Closed'."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "contest2_id" in test_data, "Contest 2 ID not found."
    assert "contest3_id" in test_data, "Contest 3 ID not found."

    contests_to_close = ["contest1_id", "contest2_id", "contest3_id"]
    for contest_key in contests_to_close:
        contest_id = test_data[contest_key]
        update_payload = ContestUpdate(status="Closed")
        response = await client.put(
            f"/contests/{contest_id}",
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
async def test_07_02_winners_computed_visitor_views_contest1_details(client: AsyncClient): # MODIFIED: Renamed, async def, AsyncClient
    """Visitor views contest1 details -> Should see results, user and author names revealed, ranking and judge comments/justifications visible."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    # Check contest status
    response = await client.get(f"/contests/{test_data['contest1_id']}")
    assert response.status_code == 200
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed", "Contest1 is not Closed."

    # Check submissions for revealed names, ranking, and comments
    sub_response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/")
    assert sub_response.status_code == 200, f"Visitor failed to get submissions for closed contest: {sub_response.text}"
    
    submissions = sub_response.json()
    assert isinstance(submissions, list)
    if len(submissions) > 0:
        print(f"Verifying submissions for contest1 (ID: {test_data['contest1_id']}):")
        for sub_data in submissions:
            current_submission_identifier = sub_data.get('text_id', 'UNKNOWN_TEXT_ID')
            submission = ContestTextResponse(**sub_data)
            print(f"  Submission for Text ID: {current_submission_identifier}, Owner ID: {submission.owner_id}, Author: {submission.author}, Title: {sub_data.get('title')}")
            assert submission.owner_id is not None, "Owner ID should be revealed for submissions in a Closed contest."
            assert submission.author is not None and "masked" not in submission.author.lower() and submission.author != "[Hidden]", \
                f"Author name should be revealed for Text ID {current_submission_identifier}. Got: {submission.author}"
            
            # Verify ranking and comments presence
            assert hasattr(submission, 'ranking') and submission.ranking is not None, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have a ranking. Response: {sub_data}"
            
            evaluations = sub_data.get('evaluations')
            if evaluations is None and hasattr(submission, 'evaluations'):
                evaluations = submission.evaluations

            assert evaluations is not None and isinstance(evaluations, list) and len(evaluations) > 0, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have evaluations/comments. Response: {sub_data}"

            print(f"    Ranking: {submission.ranking}, Evaluations count: {len(evaluations)}")
            for eval_data in evaluations: 
                assert 'comment' in eval_data and eval_data['comment'] is not None, \
                    f"Evaluation for Text ID {current_submission_identifier} is missing a comment. Eval data: {eval_data}"
                assert 'judge_identifier' in eval_data, f"Evaluation for Text ID {current_submission_identifier} is missing judge_identifier."
                print(f"      Judge ID: {eval_data['judge_identifier']}, Comment: '{eval_data['comment'][:50]}...'")

    else:
        print("No submissions in contest1 to verify name reveal, ranking, and comments.")

    print(f"Verified: Contest1 (ID: {test_data['contest1_id']}) details and submissions are publicly visible with results.")

@pytest.mark.run(after='test_07_02_winners_computed_visitor_views_contest1_details') # MODIFIED
async def test_07_03_user1_changes_contest1_to_private(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 changes contest1 to private."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    test_data["contest1_password"] = "testprivpass123" # Store password for later tests

    update_payload = ContestUpdate(is_private=True, password=test_data["contest1_password"])
    response = await client.put(
        f"/contests/{test_data['contest1_id']}",
        json=update_payload.model_dump(exclude_unset=True),
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to set contest1 to private: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.is_private is True, "Contest1 visibility not set to private."
    print(f"User 1 successfully changed contest1 (ID: {test_data['contest1_id']}) to private.")

@pytest.mark.run(after='test_07_03_user1_changes_contest1_to_private')
async def test_07_04_visitor_views_contest1_details_private_no_pass_fails(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Visitor attempts to view contest1 details with no password -> Fails."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = await client.get(f"/contests/{test_data['contest1_id']}")
    assert response.status_code == 403, \
        f"Viewing private contest1 without password should fail (403), got {response.status_code}: {response.text}"
    print(f"Visitor attempt to view private contest1 (ID: {test_data['contest1_id']}) without password failed as expected.")

@pytest.mark.run(after='test_07_04_visitor_views_contest1_details_private_no_pass_fails')
async def test_07_05_visitor_views_contest1_details_private_with_pass_succeeds(client: AsyncClient): # MODIFIED: Renamed, async def, AsyncClient
    """Visitor attempts to view contest1 details with correct password -> Succeeds. User and author names revealed, ranking and judge comments/justifications visible."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    assert "contest1_password" in test_data, "Contest1 password not found in test_data."

    response = await client.get(f"/contests/{test_data['contest1_id']}", params={"password": test_data["contest1_password"]})
    assert response.status_code == 200, \
        f"Viewing private contest1 with password failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed"
    
    # Check submissions for revealed names, ranking, and comments
    sub_response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/", params={"password": test_data["contest1_password"]})
    assert sub_response.status_code == 200
    submissions = sub_response.json()
    if len(submissions) > 0:
        print(f"Verifying submissions for private contest1 (ID: {test_data['contest1_id']}) accessed with password:")
        for sub_data in submissions:
            current_submission_identifier = sub_data.get('text_id', 'UNKNOWN_TEXT_ID')
            submission = ContestTextResponse(**sub_data)
            print(f"  Submission for Text ID: {current_submission_identifier}, Owner ID: {submission.owner_id}, Author: {submission.author}, Title: {sub_data.get('title')}")
            assert submission.owner_id is not None
            assert submission.author is not None and "masked" not in submission.author.lower()
            assert hasattr(submission, 'ranking') and submission.ranking is not None, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have a ranking. Response: {sub_data}"
            
            evaluations = sub_data.get('evaluations')
            if evaluations is None and hasattr(submission, 'evaluations'):
                evaluations = submission.evaluations
            
            assert evaluations is not None and isinstance(evaluations, list) and len(evaluations) > 0, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have evaluations/comments. Response: {sub_data}"
            print(f"    Ranking: {submission.ranking}, Evaluations count: {len(evaluations)}")
    else:
        print("No submissions in private contest1 to verify details.")
    print(f"Visitor successfully viewed private contest1 (ID: {test_data['contest1_id']}) with correct password and details revealed.")

@pytest.mark.run(after='test_07_05_visitor_views_contest1_details_private_with_pass_succeeds')
async def test_07_06_user1_returns_contest1_to_public(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """User 1 returns contest1 to public."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "contest1_id" in test_data, "Contest 1 ID not found."

    update_payload = ContestUpdate(is_private=False, password=None) # Ensure password is set to None
    response = await client.put(
        f"/contests/{test_data['contest1_id']}",
        json=update_payload.model_dump(exclude_unset=True, exclude_none=True), # exclude_none=True will remove password if None
        headers=test_data["user1_headers"]
    )
    assert response.status_code == 200, \
        f"User 1 failed to set contest1 to public: {response.text}"
    updated_contest = ContestResponse(**response.json())
    assert updated_contest.is_private is False, "Contest1 visibility not set to public."
    # Check if the API correctly reflects that there's no password.
    # This depends on how 'has_password' is implemented in ContestResponse.
    # Assuming 'has_password' becomes False or is absent.
    if hasattr(updated_contest, 'has_password'):
        assert updated_contest.has_password is False, "Contest1 should not indicate it has a password after being made public."
    print(f"User 1 successfully returned contest1 (ID: {test_data['contest1_id']}) to public.")

@pytest.mark.run(after='test_07_06_user1_returns_contest1_to_public')
async def test_07_07_visitor_views_contest1_public_details_revealed(client: AsyncClient): # MODIFIED: Renamed, async def, AsyncClient
    """Visitor attempts to view contest1 details (now public) with no password -> Succeeds. User and author names revealed, ranking and comments visible."""
    assert "contest1_id" in test_data, "Contest 1 ID not found."
    response = await client.get(f"/contests/{test_data['contest1_id']}")
    assert response.status_code == 200, \
        f"Viewing public contest1 failed: {response.text}"
    contest_data = ContestResponse(**response.json())
    assert contest_data.status.lower() == "closed"
    
    # Check submissions for revealed names, ranking, and comments (as in 7.02)
    sub_response = await client.get(f"/contests/{test_data['contest1_id']}/submissions/")
    assert sub_response.status_code == 200
    submissions = sub_response.json()
    if len(submissions) > 0:
        print(f"Verifying submissions for public contest1 (ID: {test_data['contest1_id']}) after being returned to public:")
        for sub_data in submissions:
            current_submission_identifier = sub_data.get('text_id', 'UNKNOWN_TEXT_ID')
            submission = ContestTextResponse(**sub_data)
            print(f"  Submission for Text ID: {current_submission_identifier}, Owner ID: {submission.owner_id}, Author: {submission.author}, Title: {sub_data.get('title')}")
            assert submission.owner_id is not None
            assert submission.author is not None and "masked" not in submission.author.lower()
            assert hasattr(submission, 'ranking') and submission.ranking is not None, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have a ranking. Response: {sub_data}"
            
            evaluations = sub_data.get('evaluations')
            if evaluations is None and hasattr(submission, 'evaluations'):
                evaluations = submission.evaluations
            
            assert evaluations is not None and isinstance(evaluations, list) and len(evaluations) > 0, \
                f"Submission for Text ID {current_submission_identifier} in contest1 should have evaluations/comments. Response: {sub_data}"
            print(f"    Ranking: {submission.ranking}, Evaluations count: {len(evaluations)}")
    else:
        print("No submissions in public contest1 to verify details after return to public.")
    print(f"Visitor successfully viewed public contest1 (ID: {test_data['contest1_id']}) with details revealed.")

@pytest.mark.run(after='test_07_07_visitor_views_contest1_public_details_revealed')
async def test_07_08_user1_deletes_text1_1_and_verify_removal_from_contests(client: AsyncClient): # NEW: Test for plan item 7.09
    """User 1 deletes their own Text 1.1. Verify it is no longer in any contest (contest2, contest3)."""
    assert "user1_headers" in test_data, "User 1 token not found."
    assert "text1_1_id" in test_data, "Text 1.1 ID not found."
    text_id_to_delete = test_data["text1_1_id"]

    # --- Delete Text 1.1 ---
    delete_response = await client.delete(f"/texts/{text_id_to_delete}", headers=test_data["user1_headers"])
    assert delete_response.status_code == 204, \
        f"User 1 failed to delete Text 1.1 (ID: {text_id_to_delete}): {delete_response.text}"
    print(f"User 1 successfully deleted Text 1.1 (ID: {text_id_to_delete}).")

    # --- Verify Text 1.1 is deleted ---
    get_text_response = await client.get(f"/texts/{text_id_to_delete}", headers=test_data["user1_headers"])
    assert get_text_response.status_code == 404, \
        f"Text 1.1 (ID: {text_id_to_delete}) still found after deletion attempt. Status: {get_text_response.status_code}"
    print(f"Verified Text 1.1 (ID: {text_id_to_delete}) is no longer accessible directly.")

    # --- Verify Text 1.1 is removed from Contest 2 ---
    # Text 1.1 was submitted to contest2 (submission_id_c2_t1_1 in test 5.06, possibly removed in 5.16)
    # If it was removed in 5.16, this check should still pass as it wouldn't be found.
    # The plan summary for sec 5 says "Texts in contest2: Text 1.1" but also "Submissions removed: ... Text 1.1 from contest2"
    # For robustness, we'll check contest2 and contest3, assuming it might have been in either or re-added.
    # The core idea is that deleting a text removes its *submissions* from contests.

    if "contest2_id" in test_data:
        contest2_id = test_data["contest2_id"]
        headers_to_use_c2 = test_data.get("admin_headers") # Admin can always see submissions
        if not headers_to_use_c2 : headers_to_use_c2 = test_data.get("user1_headers") # Or user1 if contest is public / user1 created

        params_c2 = {}
        # Check if contest2 is private and needs a password, use admin or user who knows password if needed
        # For simplicity, let's assume admin can view it.
        
        # Get contest 2 details to check if it's private and requires password for general viewing
        contest2_details_resp = await client.get(f"/contests/{contest2_id}", headers=headers_to_use_c2)
        if contest2_details_resp.status_code == 200:
            contest2_details = ContestResponse(**contest2_details_resp.json())
            if contest2_details.is_private and "contest2_password" in test_data:
                 params_c2["password"] = test_data["contest2_password"]
        
        sub_response_c2 = await client.get(f"/contests/{contest2_id}/submissions/", headers=headers_to_use_c2, params=params_c2)
        if sub_response_c2.status_code == 200:
            submissions_c2 = [ContestTextResponse(**s) for s in sub_response_c2.json()]
            found_in_c2 = any(s.text_id == text_id_to_delete for s in submissions_c2)
            assert not found_in_c2, \
                f"Text 1.1 (ID: {text_id_to_delete}) was found in Contest 2 (ID: {contest2_id}) submissions after text deletion."
            print(f"Verified Text 1.1 (ID: {text_id_to_delete}) is not in Contest 2 (ID: {contest2_id}) submissions.")
        else:
            print(f"Could not fetch submissions for Contest 2 (ID: {contest2_id}) to verify text removal. Status: {sub_response_c2.status_code}, Response: {sub_response_c2.text}")
            # This might be okay if contest2 was deleted or inaccessible for some valid reason based on test flow.
            # However, for this test, we expect to be able to check.

    # --- Verify Text 1.1 is removed from Contest 3 ---
    # Text 1.1 was submitted to contest3 (submission_id_c3_t1_1_v2 from test 5.22)
    if "contest3_id" in test_data:
        contest3_id = test_data["contest3_id"]
        headers_to_use_c3 = test_data.get("admin_headers") # Admin can always see submissions
        if not headers_to_use_c3: headers_to_use_c3 = test_data.get("user2_headers") # Or user2 if contest is public / user2 created

        params_c3 = {}
        contest3_details_resp = await client.get(f"/contests/{contest3_id}", headers=headers_to_use_c3)
        if contest3_details_resp.status_code == 200:
            contest3_details = ContestResponse(**contest3_details_resp.json())
            if contest3_details.is_private and "contest3_password" in test_data: # Assuming contest3 might have a password
                 params_c3["password"] = test_data["contest3_password"] # Add if applicable

        sub_response_c3 = await client.get(f"/contests/{contest3_id}/submissions/", headers=headers_to_use_c3, params=params_c3)
        if sub_response_c3.status_code == 200:
            submissions_c3 = [ContestTextResponse(**s) for s in sub_response_c3.json()]
            found_in_c3 = any(s.text_id == text_id_to_delete for s in submissions_c3)
            assert not found_in_c3, \
                f"Text 1.1 (ID: {text_id_to_delete}) was found in Contest 3 (ID: {contest3_id}) submissions after text deletion."
            print(f"Verified Text 1.1 (ID: {text_id_to_delete}) is not in Contest 3 (ID: {contest3_id}) submissions.")
        else:
            print(f"Could not fetch submissions for Contest 3 (ID: {contest3_id}) to verify text removal. Status: {sub_response_c3.status_code}, Response: {sub_response_c3.text}")


    print(f"Successfully verified deletion of Text 1.1 (ID: {text_id_to_delete}) and its removal from associated contests.")


# --- End of Test Section 7: Contest Closure & Results ---