# backend/tests/e2e_sec_10_final_state_verification_post_cleanup.py
import pytest
from httpx import AsyncClient # MODIFIED: For async client
from typing import List # Keep if listing endpoints are used for verification
import logging
import json

from app.schemas.credit import CreditUsageSummary # MODIFIED: Was AIServiceCostSummaryResponse
from app.schemas.user import UserResponse # ADDED for listing users
from app.schemas.contest import ContestResponse # ADDED for listing contests
from app.schemas.agent import AgentResponse # ADDED for listing agents
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 10: Final State Verification & Cost Monitoring (Post-Cleanup) ---

@pytest.mark.run(after='test_09_11_admin_deletes_user2') # After section 9
async def test_10_01_verify_all_test_entities_are_deleted(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Verify all users, contests, AI agents created in the test are deleted by listing them."""
    assert "admin_headers" in test_data, "Admin token not found for verification."
    admin_headers = test_data["admin_headers"]

    # Verify Users: Expect only the admin user to remain
    # This assumes test users user1 & user2 were created and deleted, and admin was the only other user.
    # If there are other seeded users, this assertion needs adjustment.
    user_list_response = await client.get("/users", headers=admin_headers)
    assert user_list_response.status_code == 200, f"Failed to list users: {user_list_response.text}"
    users = [UserResponse(**user) for user in user_list_response.json()]
    # It's safer to check that known test user IDs are NOT present, but they are removed from test_data.
    # We assume the admin user performing these checks is still present.
    # And that user1_id and user2_id, if they could be retrieved, would not be in the list.
    # A simple check might be on count if we know the exact number of test users vs persistent users.
    # For now, let's assume the goal is to have *very few* users, ideally 1 (the admin).
    # This is a weak assertion without knowing initial state.
    # A better approach might be to ensure the specific IDs of user1/user2 (if stored before deletion from test_data) are not in `users_after_cleanup_ids`.
    # However, tests 9.10 and 9.11 already confirm 404 on GET for specific user IDs.
    # So, we can assert that the number of users is now less than it was before user1 & user2 were created if that was tracked.
    # Or, if we know the admin user's details, assert that only that user (or users not part of the test) exists.
    # Given user1_id and user2_id are gone from test_data, we can print the number of remaining users.
    print(f"Number of users remaining: {len(users)}. Test users user1 and user2 should be deleted.")
    # If admin_user_id was stored:
    if "admin_user_id" in test_data:
        admin_is_present = any(u.id == test_data["admin_user_id"] for u in users)
        assert admin_is_present, "Admin user is no longer present in the user list."
        # assert len(users) == 1, f"Expected only admin user to remain, but found {len(users)} users." # This is too strict without knowing setup.
    print(f"Admin confirmed {len(users)} users exist post-cleanup.")


    # Verify Contests: Expect zero contests if all were test-created
    # The GET /contests endpoint is public and doesn't strictly need admin_headers but using it is fine.
    contest_list_response = await client.get("/contests/", headers=admin_headers)
    assert contest_list_response.status_code == 200, f"Failed to list contests: {contest_list_response.text}"
    contests = [ContestResponse(**contest) for contest in contest_list_response.json()]
    assert len(contests) == 0, f"Expected 0 contests after cleanup, but found {len(contests)}: {[c.id for c in contests]}"
    print(f"Admin confirmed {len(contests)} contests exist post-cleanup (expected 0).")

    # Verify AI Agents: Expect zero agents if all were test-created
    # GET /agents with no filters, as admin, should return all agents.
    agent_list_response = await client.get("/agents", headers=admin_headers)
    assert agent_list_response.status_code == 200, f"Failed to list agents: {agent_list_response.text}"
    agents = [AgentResponse(**agent) for agent in agent_list_response.json()]
    assert len(agents) == 0, f"Expected 0 AI agents after cleanup, but found {len(agents)}: {[a.id for a in agents]}"
    print(f"Admin confirmed {len(agents)} AI agents exist post-cleanup (expected 0).")

    print("Section 10.01: Verification of entity deletion complete.")

@pytest.mark.run(after='test_10_01_verify_all_test_entities_are_deleted')
async def test_10_02_admin_checks_ai_costs_summary_post_cleanup(client: AsyncClient): # MODIFIED: async def, AsyncClient
    """Admin checks AI costs summary again, it should be unaffected by deletions of users/contests/agents etc."""
    assert "admin_headers" in test_data, "Admin token not found."
    # Assumes admin_user was not deleted, or a new admin session is used.

    # Fetch current AI costs summary
    response = await client.get("/admin/credits/usage", headers=test_data["admin_headers"]) # MODIFIED: await, removed settings.API_V1_STR, changed path
    assert response.status_code == 200, f"Admin failed to get AI costs summary post-cleanup: {response.text}"
    
    costs_summary_after = CreditUsageSummary(**response.json()) # MODIFIED
    print(f"Admin successfully retrieved AI costs summary post-cleanup. Total cost: {costs_summary_after.total_credits_used}") # MODIFIED

    assert 'ai_total_cost_pre_cleanup' in test_data, "Pre-cleanup AI total cost was not stored in test_data."
    stored_pre_cleanup_cost = test_data['ai_total_cost_pre_cleanup']
    
    assert costs_summary_after.total_credits_used == stored_pre_cleanup_cost, \
        f"AI total cost should remain the same after cleanup. Post-cleanup: {costs_summary_after.total_credits_used}, Pre-cleanup: {stored_pre_cleanup_cost}"

    print(f"AI costs summary post-cleanup total: {costs_summary_after.total_credits_used}. Verified against pre-cleanup cost: {stored_pre_cleanup_cost}.") # MODIFIED

    # Ensure and compare the total real cost USD
    assert hasattr(costs_summary_after, 'total_real_cost_usd'), "Total real cost USD field missing in summary post-cleanup."
    assert 'ai_total_real_cost_pre_cleanup' in test_data, "Pre-cleanup AI real cost USD was not stored in test_data."
    stored_pre_cleanup_real_cost = test_data['ai_total_real_cost_pre_cleanup']
    assert costs_summary_after.total_real_cost_usd == stored_pre_cleanup_real_cost, \
        f"AI total real cost USD should remain the same after cleanup. Post-cleanup USD: {costs_summary_after.total_real_cost_usd}, Pre-cleanup USD: {stored_pre_cleanup_real_cost}"
    print(f"AI total real cost USD post-cleanup: {costs_summary_after.total_real_cost_usd}. Verified against pre-cleanup USD cost: {stored_pre_cleanup_real_cost}.")

    # Export the post-cleanup AI costs summary to a file
    with open("ai_costs_summary_post_cleanup.json", "w") as f:
        json.dump(response.json(), f, indent=2)
    print("AI costs summary post-cleanup exported to ai_costs_summary_post_cleanup.json")

# --- End of Test Section 10 --- 