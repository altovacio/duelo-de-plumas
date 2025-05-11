# backend/tests/e2e_sec_08_cost_usage_monitoring_pre_cleanup.py
import pytest
from fastapi.testclient import TestClient # Injected by fixture
from typing import List # Added for type hinting
import logging

from app.core.config import settings
# Add relevant schemas for cost/credit history if any direct API calls are made
# from backend.app.schemas.credit import CreditLogResponse, AIServiceCostSummaryResponse
from app.schemas.user import UserResponse # For balance checks
from app.schemas.credit import CreditTransactionResponse, CreditUsageSummary # MODIFIED: Was AIServiceCostSummaryResponse
from tests.shared_test_state import test_data

# client will be a fixture argument to test functions

# --- Start of Test Section 8: Cost & Usage Monitoring (Pre-Cleanup) ---

@pytest.mark.run(after='test_07_09_user1_deletes_submission_c1_t2_2_from_contest1') # After section 7
def test_08_01_admin_checks_ai_costs_summary(client: TestClient):
    """Admin checks AI costs summary."""
    assert "admin_headers" in test_data, "Admin token not found."

    response = client.get(f"{settings.API_V1_STR}/admin/ai-costs-summary", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to get AI costs summary: {response.text}"
    
    costs_summary = CreditUsageSummary(**response.json()) # MODIFIED
    assert costs_summary.total_credits_used >= 0, "Total AI cost should be non-negative." # MODIFIED
    # Potentially more assertions based on expected costs from previous tests if tracked meticulously
    # For now, just check structure and non-negative total cost.
    print(f"Admin successfully retrieved AI costs summary. Total cost: {costs_summary.total_credits_used}, Breakdown: {costs_summary.usage_by_model}") # MODIFIED

@pytest.mark.run(after='test_08_01_admin_checks_ai_costs_summary')
def test_08_02_admin_checks_user1_credit_history(client: TestClient):
    """Admin checks User 1's credit history."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user1_id" in test_data, "User 1 ID not found."

    response = client.get(f"{settings.API_V1_STR}/admin/users/{test_data['user1_id']}/credit-history", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to get User 1 credit history: {response.text}"
    
    credit_history = response.json()
    assert isinstance(credit_history, list), "Credit history should be a list."
    # Each item should conform to CreditTransactionResponse schema
    for item in credit_history:
        transaction = CreditTransactionResponse(**item)
        assert transaction.user_id == test_data["user1_id"]
        # Further checks if specific transactions are expected
    
    print(f"Admin successfully retrieved User 1's credit history (found {len(credit_history)} transactions).")
    # Store for potential verification against user's own view or calculations
    test_data["user1_credit_history_admin_view"] = credit_history 

@pytest.mark.run(after='test_08_02_admin_checks_user1_credit_history')
def test_08_03_admin_checks_user2_credit_history(client: TestClient):
    """Admin checks User 2's credit history."""
    assert "admin_headers" in test_data, "Admin token not found."
    assert "user2_id" in test_data, "User 2 ID not found."

    response = client.get(f"{settings.API_V1_STR}/admin/users/{test_data['user2_id']}/credit-history", headers=test_data["admin_headers"])
    assert response.status_code == 200, f"Admin failed to get User 2 credit history: {response.text}"
    
    credit_history = response.json()
    assert isinstance(credit_history, list), "Credit history should be a list."
    for item in credit_history:
        transaction = CreditTransactionResponse(**item)
        assert transaction.user_id == test_data["user2_id"]

    print(f"Admin successfully retrieved User 2's credit history (found {len(credit_history)} transactions).")
    test_data["user2_credit_history_admin_view"] = credit_history

@pytest.mark.run(after='test_08_03_admin_checks_user2_credit_history')
def test_08_04_user1_checks_their_credit_balance(client: TestClient):
    """User 1 checks their credit balance."""
    assert "user1_headers" in test_data, "User 1 token not found."

    response = client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user1_headers"])
    assert response.status_code == 200, f"User 1 failed to get their details: {response.text}"
    
    user_details = UserResponse(**response.json())
    # We can store this if we want to compare it with a calculated balance from history
    test_data["user1_final_balance_self_view"] = user_details.credits
    print(f"User 1 successfully checked their credit balance: {user_details.credits}.")
    # Add assertion for expected balance if calculations are done through the tests
    # For example, if initial_credits - sum(costs) + sum(additions) is tracked.

@pytest.mark.run(after='test_08_04_user1_checks_their_credit_balance')
def test_08_05_user2_checks_their_credit_balance(client: TestClient):
    """User 2 checks their credit balance."""
    assert "user2_headers" in test_data, "User 2 token not found."

    response = client.get(f"{settings.API_V1_STR}/users/me", headers=test_data["user2_headers"])
    assert response.status_code == 200, f"User 2 failed to get their details: {response.text}"
    
    user_details = UserResponse(**response.json())
    test_data["user2_final_balance_self_view"] = user_details.credits
    print(f"User 2 successfully checked their credit balance: {user_details.credits}.")

# --- End of Test Section 8 --- 