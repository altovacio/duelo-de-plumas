"""
End-to-End tests for User-Owned AI Agents and Credit/Cost System.

Covers:
- User 1 creates an AI Writer.
- User 1 creates an AI Judge.
- User 1 creates a Contest.
- User 1 attempts to generate text with their AI Writer (insufficient credits - expect 402).
- Admin assigns credits to User 1.
- User 1 generates text with the AI Writer (sufficient credits).
    - Use a cost-effective model like Claude Haiku if making real API calls.
    - Verify successful response.
    - Verify text is generated (content check optional).
    - Verify credits are deducted correctly from User 1 balance.
    - Verify CostLedger entry is created for User 1 with correct details (action, cost, balance, entity). 
        - Note: Consider adding a test identifier to the description or using dedicated test users if ledger differentiation is crucial.
- User 1 submits generated text (or placeholder) to their Contest.
- User 1 attempts to evaluate their contest with their AI Judge (insufficient credits).
- User 1 evaluates the contest with the AI Judge (sufficient credits).
    - Use a cost-effective model like Claude Haiku if making real API calls.
    - Verify successful response.
    - Verify votes are created (check DB or potentially a specific endpoint if available).
    - Verify credits are deducted correctly.
    - Verify CostLedger entry is created correctly.
- Admin views User 1's credit history (CostLedger entries).
- Create User 2.
- User 2 attempts to trigger User 1's AI Writer (expect 403 Forbidden).
- User 2 attempts to trigger User 1's AI Judge (expect 403 Forbidden).
- Test deletion of User 1's AI agents.
- Test deletion of User 1 and verify their CostLedger entries remain.
- Test deletion of User 2.
"""

import pytest
import httpx
import os # Added for environment variables
from uuid import uuid4
from dotenv import load_dotenv # Added for .env loading

# Load environment variables from .env file
load_dotenv()

# Assume backend runs on localhost:8000
BASE_URL = "http://localhost:8000"
# Define the model ID used for testing consistently
TEST_MODEL_ID = "claude-3-5-haiku-latest"

# --- Helper Functions ---

async def create_user(client: httpx.AsyncClient, username: str, password: str, email: str, role: str = "user"):
    """Helper to create a user via admin endpoint."""
    # Requires admin credentials - assuming we have them or can get them
    # TODO: Implement admin login or use a fixture for admin client
    admin_token = "YOUR_ADMIN_TOKEN" # Replace with actual admin token retrieval
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Note: Based on api_roles_and_features.md, admin user creation needs update
    # Assuming it takes username, password, email for now. Role setting might differ.
    # POST /admin/users/ might be the endpoint (needs clarification/update in docs)
    # Let's use POST /auth/register for now, assuming it can be used, 
    # although admin might be needed later for credit assignment.
    # If registration gives 0 credits, that aligns with the plan.
    
    # Using registration endpoint instead of admin for initial creation
    register_data = {"username": username, "email": email, "password": password}
    response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
    
    # Check if user already exists, handle gracefully for tests
    if response.status_code == 400 and "already exists" in response.text:
        print(f"User {username} might already exist. Proceeding...")
        # Attempt login to get user details if needed
        login_response = await login_user(client, username, password)
        if login_response.status_code == 200:
             # We need the user ID later for admin actions
             # Let's get it from the /me endpoint
             me_response = await client.get(f"{BASE_URL}/auth/users/me", headers={"Authorization": f"Bearer {login_response.json()['access_token']}"})
             if me_response.status_code == 200:
                 return me_response.json() # Return user details including ID
             else:
                 raise Exception(f"Failed to get user details for existing user {username}: {me_response.status_code} {me_response.text}")
        else:
             raise Exception(f"Failed to login existing user {username}: {login_response.status_code} {login_response.text}")

    elif response.status_code != 201: # Expect 201 Created from register
        raise Exception(f"Failed to create user {username}: {response.status_code} {response.text}")
        
    return response.json() # Return created user details (might include ID)

async def login_user(client: httpx.AsyncClient, username: str, password: str):
    """Helper to login a user and get token."""
    login_data = {"username": username, "password": password}
    # Using form data as per OAuth2 standard for /token endpoint
    response = await client.post(f"{BASE_URL}/auth/token", data=login_data)
    return response

# --- Test Fixtures ---

@pytest.fixture(scope="module")
async def async_client():
    async with httpx.AsyncClient() as client:
        yield client

@pytest.fixture(scope="module")
async def user1_credentials():
    return {
        "username": "test_user1",
        "password": "password123",
        "email": "test_user1@test.plumas.top"
    }

@pytest.fixture(scope="module")
async def user2_credentials():
    return {
        "username": "test_user2",
        "password": "password456",
        "email": "test_user2@test.plumas.top"
    }
    
# Placeholder for admin client/token - needs proper setup
@pytest.fixture(scope="module")
async def admin_token(async_client):
     admin_username = os.getenv("ADMIN_USERNAME")
     admin_password = os.getenv("ADMIN_PASSWORD")
     
     if not admin_username or not admin_password:
         pytest.skip("ADMIN_USERNAME and ADMIN_PASSWORD environment variables not set. Skipping tests requiring admin.")
         return None # Or raise an error if admin is strictly required

     print(f"Attempting admin login for user: {admin_username}")
     admin_login_response = await login_user(async_client, admin_username, admin_password)
     
     if admin_login_response.status_code != 200:
         pytest.fail(f"Failed to login admin user '{admin_username}': {admin_login_response.status_code} {admin_login_response.text}")
         
     token = admin_login_response.json().get("access_token")
     if not token:
         pytest.fail("Admin login successful but no access token found in response.")
         
     print("Admin login successful.")
     return token

# --- Test Class ---

@pytest.mark.asyncio
class TestAICostsE2E:

    user1_id: int = None
    user1_token: str = None
    user1_writer_id: int = None
    user1_judge_id: int = None
    user1_contest_id: int = None
    user1_initial_credits: int = 0 # Start with 0
    user1_credits_after_add: int = 10000 # Define how many credits admin adds
    user1_generate_cost: int = None
    user1_balance_after_generate: int = None
    user1_evaluate_cost: int = None
    user1_balance_after_evaluate: int = None

    user2_id: int = None
    user2_token: str = None

    async def test_01_setup_user1(self, async_client, user1_credentials):
        """Create User 1 and log them in."""
        print(f"Attempting to create User 1: {user1_credentials['username']}")
        # Use registration endpoint first
        response = await async_client.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": user1_credentials["username"],
                "email": user1_credentials["email"],
                "password": user1_credentials["password"],
            }
        )
        # Handle potential existing user from previous runs if needed
        if response.status_code == 400 and "already exists" in response.text:
             print(f"User {user1_credentials['username']} might already exist. Attempting login.")
        elif response.status_code != 201:
            pytest.fail(f"Failed to register user 1: {response.status_code} {response.text}")
        
        # Log in User 1
        login_response = await login_user(
            async_client, user1_credentials["username"], user1_credentials["password"]
        )
        assert login_response.status_code == 200, f"Failed to login User 1: {login_response.text}"
        TestAICostsE2E.user1_token = login_response.json()["access_token"]
        assert TestAICostsE2E.user1_token is not None

        # Get User 1 ID from /me endpoint
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        me_response = await async_client.get(f"{BASE_URL}/auth/users/me", headers=headers)
        assert me_response.status_code == 200, f"Failed to get User 1 details: {me_response.text}"
        user_details = me_response.json()
        TestAICostsE2E.user1_id = user_details.get("id")
        assert TestAICostsE2E.user1_id is not None
        # Verify initial credit balance is 0 (as per description_utopia_v2.md)
        TestAICostsE2E.user1_initial_credits = user_details.get("credits", 0) # Store initial credits
        assert TestAICostsE2E.user1_initial_credits == 0, f"User 1 initial credits should be 0, but got {TestAICostsE2E.user1_initial_credits}"
        print(f"User 1 ({user1_credentials['username']}, ID: {TestAICostsE2E.user1_id}) created and logged in with {TestAICostsE2E.user1_initial_credits} credits.")

    async def test_02_user1_create_ai_writer(self, async_client):
        """User 1 creates an AI Writer."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        writer_data = {
            "name": f"TestWriter_{uuid4()}",
            "description": "A writer for E2E tests",
            "personality_prompt": "You are a helpful test writer."
            # Assuming base_prompt is set by backend or not needed for creation
        }
        response = await async_client.post(f"{BASE_URL}/ai-writers", headers=headers, json=writer_data)
        assert response.status_code == 201, f"Failed to create AI Writer: {response.status_code} {response.text}"
        writer_details = response.json()
        TestAICostsE2E.user1_writer_id = writer_details.get("id")
        assert TestAICostsE2E.user1_writer_id is not None
        print(f"User 1 created AI Writer ID: {TestAICostsE2E.user1_writer_id}")

    async def test_03_user1_create_ai_judge(self, async_client):
        """User 1 creates an AI Judge."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        judge_data = {
            "name": f"TestJudge_{uuid4()}",
            "description": "A judge for E2E tests",
            "personality_prompt": "You are a fair test judge."
        }
        response = await async_client.post(f"{BASE_URL}/ai-judges", headers=headers, json=judge_data)
        assert response.status_code == 201, f"Failed to create AI Judge: {response.status_code} {response.text}"
        judge_details = response.json()
        TestAICostsE2E.user1_judge_id = judge_details.get("id")
        assert TestAICostsE2E.user1_judge_id is not None
        print(f"User 1 created AI Judge ID: {TestAICostsE2E.user1_judge_id}")
        
    async def test_04_user1_create_contest(self, async_client):
        """User 1 creates a Contest."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        contest_data = {
            "title": f"E2E Test Contest {uuid4()}",
            "description": "## Contest for E2E testing\n\nSubmit your best test text.",
            "is_public": True 
            # Add other required fields if necessary based on ContestCreate schema
        }
        response = await async_client.post(f"{BASE_URL}/contests/", headers=headers, json=contest_data)
        assert response.status_code == 201, f"Failed to create Contest: {response.status_code} {response.text}"
        contest_details = response.json()
        TestAICostsE2E.user1_contest_id = contest_details.get("id")
        assert TestAICostsE2E.user1_contest_id is not None
        print(f"User 1 created Contest ID: {TestAICostsE2E.user1_contest_id}")

    async def test_05_user1_generate_insufficient_credits(self, async_client):
        """User 1 attempts AI generation with 0 credits (expect 402)."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_writer_id, "User 1 writer ID not available"
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        # Assuming Claude Haiku is a valid, cheap model ID recognized by the backend
        generate_data = {"model_id": TEST_MODEL_ID} 
        
        url = f"{BASE_URL}/ai-writers/{TestAICostsE2E.user1_writer_id}/generate"
        print(f"Attempting generation (expect fail): POST {url}")
        response = await async_client.post(url, headers=headers, json=generate_data)
        
        # Expect 402 Payment Required
        assert response.status_code == 402, f"Expected 402 Payment Required, but got {response.status_code}: {response.text}"
        print("Received expected 402 for insufficient credits.")

    async def test_06_admin_assigns_credits(self, async_client, admin_token):
        """Admin assigns credits to User 1."""
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Use the defined credit amount
        credit_data = {"credits": TestAICostsE2E.user1_credits_after_add}
        
        url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credits"
        print(f"Admin assigning {TestAICostsE2E.user1_credits_after_add} credits to User ID {TestAICostsE2E.user1_id}: PUT {url}")
        response = await async_client.put(url, headers=headers, json=credit_data)
        
        assert response.status_code == 200, f"Failed to assign credits: {response.status_code} {response.text}"
        updated_user_details = response.json()
        # Verify the balance in the response is correct
        assert updated_user_details.get("credits") == TestAICostsE2E.user1_credits_after_add, \
               f"Expected {TestAICostsE2E.user1_credits_after_add} credits, but API returned {updated_user_details.get('credits')}"
        print(f"Successfully assigned credits. User 1 balance is now {updated_user_details.get('credits')}.")
        
    async def test_07_user1_generate_sufficient_credits(self, async_client):
        """User 1 generates text with the AI Writer (sufficient credits)."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_writer_id, "User 1 writer ID not available"
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        # Use a cost-effective model ID assumed to be configured in the backend
        generate_data = {"model_id": TEST_MODEL_ID}
        
        url = f"{BASE_URL}/ai-writers/{TestAICostsE2E.user1_writer_id}/generate"
        print(f"Attempting generation (expect success): POST {url}")
        response = await async_client.post(url, headers=headers, json=generate_data)
        
        assert response.status_code == 200, f"AI generation failed: {response.status_code} {response.text}"
        
        response_data = response.json()
        print(f"Generation successful. Response: {response_data}")
        
        # Verify expected fields in response
        assert "generated_text" in response_data
        assert len(response_data["generated_text"]) > 0, "Generated text is empty"
        assert "credits_spent" in response_data
        assert "remaining_credits" in response_data
        assert "cost_ledger_id" in response_data
        
        TestAICostsE2E.user1_generate_cost = response_data["credits_spent"]
        TestAICostsE2E.user1_balance_after_generate = response_data["remaining_credits"]
        
        assert TestAICostsE2E.user1_generate_cost > 0, "Credits spent should be positive"
        expected_remaining = TestAICostsE2E.user1_credits_after_add - TestAICostsE2E.user1_generate_cost
        assert TestAICostsE2E.user1_balance_after_generate == expected_remaining, \
               f"Remaining credits mismatch. Expected {expected_remaining}, got {TestAICostsE2E.user1_balance_after_generate}"
        print(f"Generation cost {TestAICostsE2E.user1_generate_cost} credits. Remaining balance: {TestAICostsE2E.user1_balance_after_generate}.")

    async def test_08_verify_credit_deduction_and_ledger(self, async_client, admin_token):
        """Verify credits are deducted correctly and CostLedger entry exists."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        assert TestAICostsE2E.user1_balance_after_generate is not None, "Previous test did not set balance after generate"
        assert TestAICostsE2E.user1_generate_cost is not None, "Previous test did not set generate cost"
        
        # 1. Verify User 1's current balance via /me endpoint
        print("Verifying User 1's balance via /me endpoint...")
        user_headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        me_response = await async_client.get(f"{BASE_URL}/auth/users/me", headers=user_headers)
        assert me_response.status_code == 200, f"Failed to get User 1 details: {me_response.text}"
        current_balance = me_response.json().get("credits")
        assert current_balance == TestAICostsE2E.user1_balance_after_generate, \
               f"User balance incorrect. Expected {TestAICostsE2E.user1_balance_after_generate}, found {current_balance}"
        print(f"User 1 balance confirmed: {current_balance}")
        
        # 2. Verify CostLedger entry via admin endpoint
        print("Verifying CostLedger entry via admin endpoint...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        history_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credit-history"
        history_response = await async_client.get(history_url, headers=admin_headers)
        assert history_response.status_code == 200, f"Failed to get credit history: {history_response.status_code} {history_response.text}"
        
        ledger_entries = history_response.json()
        assert isinstance(ledger_entries, list), "Credit history response is not a list"
        print(f"Received {len(ledger_entries)} ledger entries.")
        
        # Find the entry corresponding to the AI generation
        # We look for the entry with the correct negative credit change and action type
        generation_entry = None
        for entry in reversed(ledger_entries): # Check recent entries first
            if entry.get("action_type") == 'ai_generate' and \
               entry.get("credits_change") == -TestAICostsE2E.user1_generate_cost and \
               entry.get("related_entity_type") == 'user_ai_writer' and \
               entry.get("related_entity_id") == TestAICostsE2E.user1_writer_id:
                generation_entry = entry
                break
                
        assert generation_entry is not None, "Could not find matching CostLedger entry for AI generation"
        print(f"Found generation CostLedger entry: {generation_entry}")
        
        # Verify details of the ledger entry
        assert generation_entry.get("user_id") == TestAICostsE2E.user1_id
        assert generation_entry.get("credits_change") == -TestAICostsE2E.user1_generate_cost
        # Ensure resulting balance in ledger matches the expected balance
        assert generation_entry.get("resulting_balance") == TestAICostsE2E.user1_balance_after_generate, \
               f"Ledger resulting balance mismatch. Expected {TestAICostsE2E.user1_balance_after_generate}, got {generation_entry.get('resulting_balance')}"
        print("CostLedger entry verified.")

    async def test_09_user1_submits_to_contest(self, async_client):
        """User 1 submits generated text (or placeholder) to their Contest."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_contest_id, "User 1 contest ID not available"
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        submission_data = {
            "title": "My E2E Submission",
            "text_content": "This is the text submitted during the end-to-end test."
            # Using placeholder text. Could potentially use the text generated in test_07 
            # if we stored it in a class variable, but keeping it simple for now.
        }
        
        url = f"{BASE_URL}/contests/{TestAICostsE2E.user1_contest_id}/submissions"
        print(f"User 1 submitting text to Contest ID {TestAICostsE2E.user1_contest_id}: POST {url}")
        response = await async_client.post(url, headers=headers, json=submission_data)
        
        assert response.status_code == 201, f"Failed to submit text: {response.status_code} {response.text}"
        submission_details = response.json()
        assert submission_details.get("contest_id") == TestAICostsE2E.user1_contest_id
        assert submission_details.get("title") == submission_data["title"]
        print(f"Successfully submitted text with Submission ID: {submission_details.get('id')}")

    async def test_10_user1_evaluate_insufficient_credits(self, async_client):
        """User 1 attempts evaluation with AI Judge (insufficient credits)."""
        # This test assumes the cost of evaluation is greater than user1_balance_after_generate
        # We might need to adjust assigned credits or mock costs if this assumption isn't reliable.
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_judge_id, "User 1 judge ID not available"
        assert TestAICostsE2E.user1_contest_id, "User 1 contest ID not available"
        assert TestAICostsE2E.user1_balance_after_generate is not None, "Balance after generate is unknown"

        print(f"Current balance before evaluation attempt: {TestAICostsE2E.user1_balance_after_generate}")
        # TODO: If the balance IS sufficient, we should skip this test or adjust credits.
        # For now, assume it is insufficient based on typical LLM costs.
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        evaluate_data = {
            "contest_id": TestAICostsE2E.user1_contest_id,
            # Use the same cost-effective model for testing
            "model_id": TEST_MODEL_ID 
        }
        
        url = f"{BASE_URL}/ai-judges/{TestAICostsE2E.user1_judge_id}/evaluate"
        print(f"Attempting evaluation (expect fail 402): POST {url}")
        response = await async_client.post(url, headers=headers, json=evaluate_data)
        
        assert response.status_code == 402, f"Expected 402 Payment Required for evaluation, but got {response.status_code}: {response.text}"
        print("Received expected 402 for insufficient credits during evaluation attempt.")

    async def test_11_admin_assigns_more_credits(self, async_client, admin_token):
        """Admin assigns more credits to User 1 for evaluation."""
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        assert TestAICostsE2E.user1_balance_after_generate is not None, "Previous balance unknown"

        # Decide how many credits to add (e.g., enough for one evaluation)
        credits_to_add = 15000 # Arbitrary amount likely sufficient for evaluation
        new_total_credits = TestAICostsE2E.user1_balance_after_generate + credits_to_add
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        # We PUT the *total* desired credits, not the amount to add
        credit_data = {"credits": new_total_credits}
        
        url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credits"
        print(f"Admin setting credits to {new_total_credits} for User ID {TestAICostsE2E.user1_id}: PUT {url}")
        response = await async_client.put(url, headers=headers, json=credit_data)
        
        assert response.status_code == 200, f"Failed to assign credits: {response.status_code} {response.text}"
        updated_user_details = response.json()
        assert updated_user_details.get("credits") == new_total_credits, \
               f"Expected {new_total_credits} credits, but API returned {updated_user_details.get('credits')}"
        
        # Update the class variable tracking the expected balance
        TestAICostsE2E.user1_credits_after_add = new_total_credits # Reusing this variable, represents current total expected
        print(f"Successfully assigned more credits. User 1 balance is now {new_total_credits}.")

    async def test_12_user1_evaluate_sufficient_credits(self, async_client):
        """User 1 evaluates the contest with the AI Judge (sufficient credits)."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_judge_id, "User 1 judge ID not available"
        assert TestAICostsE2E.user1_contest_id, "User 1 contest ID not available"
        assert TestAICostsE2E.user1_credits_after_add is not None, "Current credit balance is unknown"

        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        evaluate_data = {
            "contest_id": TestAICostsE2E.user1_contest_id,
            "model_id": TEST_MODEL_ID # Use a consistent, cheap model
        }
        
        url = f"{BASE_URL}/ai-judges/{TestAICostsE2E.user1_judge_id}/evaluate"
        print(f"Attempting evaluation (expect success): POST {url}")
        response = await async_client.post(url, headers=headers, json=evaluate_data)
        
        # TODO: Verify the expected response schema for evaluation success.
        # Assuming 200 OK for now. Might be 202 Accepted if async.
        # Assuming response contains cost info similar to generation.
        assert response.status_code == 200, f"AI evaluation failed: {response.status_code} {response.text}"
        
        response_data = response.json()
        print(f"Evaluation successful. Response: {response_data}")
        
        # Verify expected fields in response (adjust based on actual API response)
        assert "evaluation_status" in response_data # Example field
        assert response_data["evaluation_status"] == "completed" # Example value
        assert "credits_spent" in response_data
        assert "remaining_credits" in response_data
        assert "cost_ledger_id" in response_data
        
        # Store cost and balance for verification
        TestAICostsE2E.user1_evaluate_cost = response_data["credits_spent"]
        TestAICostsE2E.user1_balance_after_evaluate = response_data["remaining_credits"]
        
        assert TestAICostsE2E.user1_evaluate_cost > 0, "Evaluation credits spent should be positive"
        expected_remaining = TestAICostsE2E.user1_credits_after_add - TestAICostsE2E.user1_evaluate_cost
        assert TestAICostsE2E.user1_balance_after_evaluate == expected_remaining, \
               f"Remaining credits after evaluation mismatch. Expected {expected_remaining}, got {TestAICostsE2E.user1_balance_after_evaluate}"
        print(f"Evaluation cost {TestAICostsE2E.user1_evaluate_cost} credits. Remaining balance: {TestAICostsE2E.user1_balance_after_evaluate}.")
        
        # Optional: Verify votes were created in DB if possible/needed, or via another endpoint.
        # This might require specific admin endpoints or direct DB access setup for tests.
        # print("TODO: Add verification for vote creation if applicable.")

    async def test_13_verify_evaluation_deduction_and_ledger(self, async_client, admin_token):
        """Verify credits are deducted correctly and CostLedger entry exists for evaluation."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        assert TestAICostsE2E.user1_balance_after_evaluate is not None, "Balance after evaluation is unknown"
        assert TestAICostsE2E.user1_evaluate_cost is not None, "Evaluation cost is unknown"
        
        # 1. Verify User 1's current balance via /me endpoint
        print("Verifying User 1's balance post-evaluation via /me endpoint...")
        user_headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        me_response = await async_client.get(f"{BASE_URL}/auth/users/me", headers=user_headers)
        assert me_response.status_code == 200, f"Failed to get User 1 details: {me_response.text}"
        current_balance = me_response.json().get("credits")
        assert current_balance == TestAICostsE2E.user1_balance_after_evaluate, \
               f"User balance incorrect after evaluation. Expected {TestAICostsE2E.user1_balance_after_evaluate}, found {current_balance}"
        print(f"User 1 balance confirmed post-evaluation: {current_balance}")
        
        # 2. Verify CostLedger entry via admin endpoint
        print("Verifying evaluation CostLedger entry via admin endpoint...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        history_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credit-history"
        history_response = await async_client.get(history_url, headers=admin_headers)
        assert history_response.status_code == 200, f"Failed to get credit history: {history_response.status_code} {history_response.text}"
        
        ledger_entries = history_response.json()
        assert isinstance(ledger_entries, list), "Credit history response is not a list"
        print(f"Received {len(ledger_entries)} ledger entries.")
        
        # Find the entry corresponding to the AI evaluation
        evaluation_entry = None
        for entry in reversed(ledger_entries): # Check recent entries first
            if entry.get("action_type") == 'ai_evaluate' and \
               entry.get("credits_change") == -TestAICostsE2E.user1_evaluate_cost and \
               entry.get("related_entity_type") == 'user_ai_judge' and \
               entry.get("related_entity_id") == TestAICostsE2E.user1_judge_id: 
                # Optional: Add check for contest_id in description if available/reliable
                # if f"Contest {TestAICostsE2E.user1_contest_id}" in entry.get("description", ""):
                evaluation_entry = entry
                break
                
        assert evaluation_entry is not None, "Could not find matching CostLedger entry for AI evaluation"
        print(f"Found evaluation CostLedger entry: {evaluation_entry}")
        
        # Verify details of the ledger entry
        assert evaluation_entry.get("user_id") == TestAICostsE2E.user1_id
        assert evaluation_entry.get("credits_change") == -TestAICostsE2E.user1_evaluate_cost
        assert evaluation_entry.get("resulting_balance") == TestAICostsE2E.user1_balance_after_evaluate, \
               f"Ledger resulting balance after evaluation mismatch. Expected {TestAICostsE2E.user1_balance_after_evaluate}, got {evaluation_entry.get('resulting_balance')}"
        print("Evaluation CostLedger entry verified.")

    async def test_14_admin_views_credit_history(self, async_client, admin_token):
        """Admin views User 1's credit history (basic check)."""
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        
        print("Admin explicitly viewing User 1 credit history...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        history_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credit-history"
        history_response = await async_client.get(history_url, headers=admin_headers)
        
        assert history_response.status_code == 200, f"Failed to get credit history: {history_response.status_code} {history_response.text}"
        ledger_entries = history_response.json()
        assert isinstance(ledger_entries, list)
        # Check that we have entries corresponding to the actions performed
        # Expect at least: credit assignment, generation, credit assignment, evaluation
        assert len(ledger_entries) >= 4, f"Expected at least 4 ledger entries, found {len(ledger_entries)}"
        print(f"Successfully retrieved {len(ledger_entries)} credit history entries for User 1.")

    async def test_15_setup_user2(self, async_client, user2_credentials):
        """Create User 2 and log them in."""
        print(f"Attempting to create User 2: {user2_credentials['username']}")
        response = await async_client.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": user2_credentials["username"],
                "email": user2_credentials["email"],
                "password": user2_credentials["password"],
            }
        )
        if response.status_code == 400 and "already exists" in response.text:
             print(f"User {user2_credentials['username']} might already exist. Attempting login.")
        elif response.status_code != 201:
            pytest.fail(f"Failed to register user 2: {response.status_code} {response.text}")
        
        # Log in User 2
        login_response = await login_user(
            async_client, user2_credentials["username"], user2_credentials["password"]
        )
        assert login_response.status_code == 200, f"Failed to login User 2: {login_response.text}"
        TestAICostsE2E.user2_token = login_response.json()["access_token"]
        assert TestAICostsE2E.user2_token is not None

        # Get User 2 ID
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user2_token}"}
        me_response = await async_client.get(f"{BASE_URL}/auth/users/me", headers=headers)
        assert me_response.status_code == 200, f"Failed to get User 2 details: {me_response.text}"
        user_details = me_response.json()
        TestAICostsE2E.user2_id = user_details.get("id")
        assert TestAICostsE2E.user2_id is not None
        print(f"User 2 ({user2_credentials['username']}, ID: {TestAICostsE2E.user2_id}) created and logged in.")

    async def test_16_user2_forbidden_writer(self, async_client):
        """User 2 attempts to trigger User 1's AI Writer (expect 403 Forbidden)."""
        assert TestAICostsE2E.user2_token, "User 2 token not available"
        assert TestAICostsE2E.user1_writer_id, "User 1 writer ID not available"
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user2_token}"}
        generate_data = {"model_id": TEST_MODEL_ID} 
        url = f"{BASE_URL}/ai-writers/{TestAICostsE2E.user1_writer_id}/generate"
        
        print(f"User 2 attempting to use User 1's Writer ID {TestAICostsE2E.user1_writer_id} (expect 403): POST {url}")
        response = await async_client.post(url, headers=headers, json=generate_data)
        
        assert response.status_code == 403, f"Expected 403 Forbidden, but got {response.status_code}: {response.text}"
        print("Received expected 403 Forbidden when User 2 tries to use User 1's writer.")

    async def test_17_user2_forbidden_judge(self, async_client):
        """User 2 attempts to trigger User 1's AI Judge (expect 403 Forbidden)."""
        assert TestAICostsE2E.user2_token, "User 2 token not available"
        assert TestAICostsE2E.user1_judge_id, "User 1 judge ID not available"
        assert TestAICostsE2E.user1_contest_id, "User 1 contest ID not available"
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user2_token}"}
        evaluate_data = {
            "contest_id": TestAICostsE2E.user1_contest_id,
            "model_id": TEST_MODEL_ID
        }
        url = f"{BASE_URL}/ai-judges/{TestAICostsE2E.user1_judge_id}/evaluate"
        
        print(f"User 2 attempting to use User 1's Judge ID {TestAICostsE2E.user1_judge_id} (expect 403): POST {url}")
        response = await async_client.post(url, headers=headers, json=evaluate_data)
        
        assert response.status_code == 403, f"Expected 403 Forbidden, but got {response.status_code}: {response.text}"
        print("Received expected 403 Forbidden when User 2 tries to use User 1's judge.")

    async def test_18_delete_user1_agents(self, async_client):
        """User 1 deletes their own AI Writer and Judge."""
        assert TestAICostsE2E.user1_token, "User 1 token not available"
        assert TestAICostsE2E.user1_writer_id, "User 1 writer ID not available"
        assert TestAICostsE2E.user1_judge_id, "User 1 judge ID not available"
        
        headers = {"Authorization": f"Bearer {TestAICostsE2E.user1_token}"}
        
        # Delete writer
        writer_url = f"{BASE_URL}/ai-writers/{TestAICostsE2E.user1_writer_id}"
        print(f"User 1 deleting writer ID {TestAICostsE2E.user1_writer_id}: DELETE {writer_url}")
        writer_response = await async_client.delete(writer_url, headers=headers)
        assert writer_response.status_code == 204, f"Failed to delete writer: {writer_response.status_code} {writer_response.text}"
        print("Writer deleted successfully.")
        
        # Delete judge
        judge_url = f"{BASE_URL}/ai-judges/{TestAICostsE2E.user1_judge_id}"
        print(f"User 1 deleting judge ID {TestAICostsE2E.user1_judge_id}: DELETE {judge_url}")
        judge_response = await async_client.delete(judge_url, headers=headers)
        assert judge_response.status_code == 204, f"Failed to delete judge: {judge_response.status_code} {judge_response.text}"
        print("Judge deleted successfully.")
        
        # Verify deletion (optional but good practice)
        print("Verifying agent deletion...")
        writer_get_response = await async_client.get(writer_url, headers=headers)
        assert writer_get_response.status_code == 404, "Writer should return 404 after deletion"
        judge_get_response = await async_client.get(judge_url, headers=headers)
        assert judge_get_response.status_code == 404, "Judge should return 404 after deletion"
        print("Agent deletion verified.")

    async def test_19_delete_user1_verify_ledger(self, async_client, admin_token):
        """Admin deletes User 1 and verifies their CostLedger entries remain."""
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user1_id, "User 1 ID not available"
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get history *before* deleting user
        history_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}/credit-history"
        history_response_before = await async_client.get(history_url, headers=admin_headers)
        assert history_response_before.status_code == 200
        ledger_count_before = len(history_response_before.json())
        print(f"Found {ledger_count_before} ledger entries for User 1 before deletion.")
        assert ledger_count_before > 0, "Expected ledger entries before deletion"
        
        # Delete User 1
        delete_user_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user1_id}"
        print(f"Admin deleting User ID {TestAICostsE2E.user1_id}: DELETE {delete_user_url}")
        delete_response = await async_client.delete(delete_user_url, headers=admin_headers)
        # Assuming 200 OK on successful deletion based on common practice, adjust if needed.
        assert delete_response.status_code == 200, f"Failed to delete User 1: {delete_response.status_code} {delete_response.text}"
        print("User 1 deleted successfully.")
        
        # Verify User 1 is gone (e.g., trying to get their /me should fail if logged in, or admin get fails)
        # For simplicity, we assume deletion worked based on status code.
        
        # Verify CostLedger entries STILL exist
        print("Verifying CostLedger entries exist after User 1 deletion...")
        history_response_after = await async_client.get(history_url, headers=admin_headers)
        assert history_response_after.status_code == 200, \
               f"Failed to get credit history after user deletion: {history_response_after.status_code} {history_response_after.text}"
        ledger_entries_after = history_response_after.json()
        assert isinstance(ledger_entries_after, list)
        assert len(ledger_entries_after) == ledger_count_before, \
               f"Ledger entry count changed after user deletion. Expected {ledger_count_before}, found {len(ledger_entries_after)}"
        
        # Double check the user ID is still present in the retrieved entries
        for entry in ledger_entries_after:
             assert entry.get("user_id") == TestAICostsE2E.user1_id, "Ledger entry missing original user_id"
             
        print("CostLedger entries persistence verified after User 1 deletion.")
        
    async def test_20_delete_user2(self, async_client, admin_token):
        """Admin deletes User 2."""
        assert admin_token, "Admin token not available"
        assert TestAICostsE2E.user2_id, "User 2 ID not available"
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        delete_user_url = f"{BASE_URL}/admin/users/{TestAICostsE2E.user2_id}"
        print(f"Admin deleting User ID {TestAICostsE2E.user2_id}: DELETE {delete_user_url}")
        delete_response = await async_client.delete(delete_user_url, headers=admin_headers)
        
        assert delete_response.status_code == 200, f"Failed to delete User 2: {delete_response.status_code} {delete_response.text}"
        print("User 2 deleted successfully.")

# TODO: Implement tests outlined in the docstring 
# Final cleanup or checks could be added here if needed 