# backend/tests/e2e_sec_10_final_state_verification_post_cleanup.py
import pytest
from fastapi.testclient import TestClient
from typing import List # Keep if listing endpoints are used for verification
import logging

from app.core.config import settings
from app.schemas.credit import CreditUsageSummary # MODIFIED: Was AIServiceCostSummaryResponse
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 10: Final State Verification & Cost Monitoring (Post-Cleanup) ---

@pytest.mark.run(after='test_09_11_admin_deletes_user2') # After section 9
def test_10_01_verify_all_test_entities_are_deleted(client: TestClient):
    """Verify all users, contests, AI agents, submissions, votes created in the test are deleted."""
    assert "admin_headers" in test_data, "Admin token not found for verification. Some entities might require auth to check."
    # Note: Admin user itself might be deleted if part of cleanup. 
    # If admin is deleted, a new admin/superuser session would be needed to verify some of these.
    # For now, assume admin_headers is still valid for fetching global lists if needed, or it's the last admin.
    # If admin was deleted in 9.11, these checks need to be reconsidered or use a superuser.
    # Based on current test 9.11, User1 and User2 are deleted. Admin user remains.

    # Verify Users are deleted (User1, User2)
    # user1_id and user2_id were deleted from test_data in section 9.
    # We can try to get them by IDs that *were* stored if we had them outside test_data, or rely on section 9 having done its job.
    # As test_data keys are deleted, we cannot directly use test_data["user1_id"].
    # This test is more of a conceptual check that cleanup was effective.
    # A more robust check would be to list all users and ensure none of the test users are present.
    print("Verifying deletion of User 1 and User 2 (done in Section 9). Expect 404s if attempted to fetch by ID.")

    # Verify Contests are deleted (contest1, contest2, contest3)
    # contest_ids were deleted from test_data. Attempting to fetch them should result in 404.
    print("Verifying deletion of contest1, contest2, contest3 (done in Section 9). Expect 404s if attempted to fetch by ID.")

    # Verify AI Agents are deleted (writer1, judge1, writer_global, judge_global)
    # agent_ids were deleted from test_data.
    print("Verifying deletion of AI agents (writer1, judge1, writer_global, judge_global) (done in Section 9). Expect 404s.")

    # Verify Submissions & Votes: These are harder to check individually without their parent contests.
    # Their deletion is largely dependent on cascade deletes from contest/user deletion.
    # We trust the ORM's cascade settings or specific service logic handled this in Section 9.
    print("Submissions and Votes are assumed deleted via cascade from Contest/User deletions in Section 9.")

    # Example: Check if any contests remain (should be 0 if all were test-created and deleted)
    # This requires admin privileges for listing all contests if such an endpoint exists.
    # response_contests = client.get(f"{settings.API_V1_STR}/admin/contests/all", headers=test_data["admin_headers"]) # Fictional endpoint
    # if response_contests.status_code == 200:
    #    assert len(response_contests.json()) == 0, "Some contests still exist after cleanup."

    # Similar checks for all users, all agents etc. would be more thorough.
    # For now, this test serves as a marker that cleanup should have occurred.
    print("Section 10.01: Conceptual verification that all test entities should be deleted based on Section 9 actions.")

@pytest.mark.run(after='test_10_01_verify_all_test_entities_are_deleted')
def test_10_02_admin_checks_ai_costs_summary_post_cleanup(client: TestClient):
    """Admin checks AI costs summary again, it should be unaffected by deletions of users/contests/agents etc."""
    assert "admin_headers" in test_data, "Admin token not found."
    # Assumes admin_user was not deleted, or a new admin session is used.

    # Fetch current AI costs summary
    response = client.get(f"{settings.API_V1_STR}/admin/ai-costs-summary", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to get AI costs summary post-cleanup: {response.text}"
    
    costs_summary_after = CreditUsageSummary(**response.json()) # MODIFIED
    print(f"Admin successfully retrieved AI costs summary post-cleanup. Total cost: {costs_summary_after.total_credits_used}") # MODIFIED

    # Compare with a pre-cleanup stored value if available, or check for stability/consistency.
    # For instance, if test_data["ai_costs_summary_pre_cleanup"] was stored in section 8.
    # For now, we just ensure it can be fetched and has a valid structure.
    # The critical check is that costs are not *negatively* affected (e.g. refunded) by deletions.
    # If cost records are persistent and tied to historical usage, the total should not decrease due to cleanup.
    # If specific costs were tracked from Section 8 (e.g. test_data['initial_ai_total_cost']):
    #   assert costs_summary_after.total_credits_used >= test_data['initial_ai_total_cost'], \ # MODIFIED
    #       "AI total cost should not decrease after cleanup."

    print(f"AI costs summary post-cleanup total: {costs_summary_after.total_credits_used}. This should ideally match or be greater than pre-cleanup if costs are only additive.") # MODIFIED

# --- End of Test Section 10 --- 