import requests
import pytest
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # Default if not set
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Helper function to get auth headers
def get_auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.e2e
def test_full_user_admin_workflow():
    """Runs a full end-to-end workflow test involving two users and an admin.
    
    Steps:
    --- User 1 Workflow ---
    a) Register User 1
    b) Login User 1 & Get ID
    c) List initial contests (User 1)
    d) Create public contest (User 1)
    e) Modify contest to private with password (User 1)
    f) Check password - wrong (User 1)
    g) Check password - correct & get cookie (User 1)
    h) Submit text to contest (User 1)
    i) List submissions (User 1 - expects failure)
    j) Logout User 1 (implicit)
    --- User 2 Workflow ---
    k) Register User 2
    l) Login User 2 & Get ID
    c2) List contests (User 2)
    d2) Create public contest (User 2)
    e2) Modify contest to private with password (User 2)
    f2) Check password - wrong (User 2)
    g2) Check password - correct & get cookie (User 2)
    h2) Submit text to contest (User 2)
    i2) List submissions (User 2 - expects failure)
    m) Try to delete User 1's contest (User 2 - expects failure)
    n) Logout User 2 (implicit)
    --- Cleanup Workflow ---
    o) Re-login User 1
        o1) Delete own contest (User 1)
        o2) Try to delete User 2's contest (User 1 - expects failure)
    p) Login as Admin
        p1) Delete User 1 (Admin)
        p2) Delete User 2 (Admin)
        p3) Delete User 2's contest (Admin)
    """
    user1_token = None
    user1_id = None # We might need this if the API returns it or we fetch it
    user2_token = None
    user2_id = None # We might need this
    contest1_id = None
    contest2_id = None
    submission1_id = None # Added for submission tracking
    submission2_id = None # Added for submission tracking
    admin_token = None

    print(f"\n--- Running E2E Test against {BASE_URL} ---")

    # --- User 1 Workflow ---
    print("\n--- Starting User 1 Workflow ---")
    # a) Register new user 1
    user1_data = {"username": "usertest", "email": "test@user.plumas.top", "password": "12341234"}
    print(f"Registering User 1: {user1_data['username']}")
    response = requests.post(f"{BASE_URL}/auth/register", json=user1_data)
    print(f"User 1 Registration Response: {response.status_code}, {response.text[:100]}...")
    # Handle potential conflict if user already exists from previous failed run
    if response.status_code == 400 and (
        'already registered' in response.text.lower() or 
        'user with this email already exists' in response.text.lower() or
        'user with this username already exists' in response.text.lower()
        ): # Adapt keywords as needed
        print("User 1 already exists, proceeding to login.")
    else:
        assert response.status_code == 201 # Assuming 201 Created
    # Potentially capture user1_id if returned, otherwise may need a GET /users/me later
    # Let's assume we might need user ID for admin deletion later, fetch it

    # b) Login user 1
    login_data = {"username": user1_data["username"], "password": user1_data["password"]}
    print(f"Logging in User 1: {user1_data['username']} (using username)")
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data) # Sending username, not email
    print(f"User 1 Login Response: {response.status_code}")
    assert response.status_code == 200
    user1_token = response.json().get("access_token")
    assert user1_token is not None
    print(f"User 1 Login Token obtained: {user1_token[:10]}...")
    headers_user1 = get_auth_headers(user1_token)

    # Get User 1 ID
    response = requests.get(f"{BASE_URL}/auth/users/me", headers=headers_user1)
    print(f"Get User 1 Info Response: {response.status_code}")
    assert response.status_code == 200
    user1_id = response.json().get("id")
    assert user1_id is not None
    print(f"User 1 ID: {user1_id}")

    # c) List all contests (user 1)
    print("User 1 Listing Contests...")
    response = requests.get(f"{BASE_URL}/contests/", headers=headers_user1)
    print(f"User 1 List Contests Response: {response.status_code}")
    assert response.status_code == 200
    initial_contests = response.json()

    # d) Create a new public contest (user 1)
    contest_data = {
        "title": "User1 Test Contest E2E",
        "description": "Public contest created by user 1 for E2E testing.",
        "is_public": True
    }
    print(f"User 1 Creating Contest: {contest_data['title']}")
    response = requests.post(f"{BASE_URL}/contests/", headers=headers_user1, json=contest_data)
    print(f"User 1 Create Contest Response: {response.status_code}, {response.text[:100]}...")
    assert response.status_code == 201 # Assuming 201 Created
    created_contest = response.json()
    contest1_id = created_contest.get("id")
    assert contest1_id is not None
    print(f"User 1 Created Contest ID: {contest1_id}")

    # e) Modify the contest to private with password (user 1)
    update_data = {
        "title": "User1 Test Contest E2E (Private)",
        "description": "Updated description, now private.",
        "contest_type": "private",
        "password": "qwerty",
        "status": "open"  # Explicitly keep status as open
    }
    print(f"User 1 Updating Contest {contest1_id} to Private...")
    response = requests.put(f"{BASE_URL}/contests/{contest1_id}", headers=headers_user1, json=update_data)
    print(f"User 1 Update Contest Response: {response.status_code}")
    assert response.status_code == 200

    # f) Check password with wrong password (user 1)
    check_pass_data = {"password": "wrongpassword"}
    print(f"User 1 Checking Wrong Password for Contest {contest1_id}...")
    response = requests.post(f"{BASE_URL}/contests/{contest1_id}/check-password", headers=headers_user1, json=check_pass_data)
    print(f"User 1 Check Wrong Password Response: {response.status_code}")
    assert response.status_code == 403 # Changed from 401 based on current API code

    # g) Check password with correct password (user 1)
    check_pass_data = {"password": "qwerty"}
    print(f"User 1 Checking Correct Password for Contest {contest1_id}...")
    response_g = requests.post(f"{BASE_URL}/contests/{contest1_id}/check-password", headers=headers_user1, json=check_pass_data)
    print(f"User 1 Check Correct Password Response: {response_g.status_code}, {response_g.text[:100]}...")
    assert response_g.status_code == 200
    # Capture the access cookie set by the response
    contest_access_cookie = response_g.cookies.get(f"contest_access_{contest1_id}")
    assert contest_access_cookie is not None, f"Contest access cookie for {contest1_id} not found in response."
    print(f"User 1 Obtained Contest Access Cookie: {contest_access_cookie[:10]}...")

    # Add the cookie to subsequent requests for this contest
    headers_user1_with_cookie = headers_user1.copy()
    headers_user1_with_cookie['Cookie'] = f"contest_access_{contest1_id}={contest_access_cookie}"

    # h) Submit a text to the contest (user 1)
    submission_data = {
        "title": "User1 Submission Title E2E",
        "text_content": "## Test Submission E2E\n\nThis is the content submitted by User 1."
    }
    print(f"User 1 Submitting Text to Contest {contest1_id}...")
    # Use headers WITH the contest access cookie
    response = requests.post(f"{BASE_URL}/contests/{contest1_id}/submissions", headers=headers_user1_with_cookie, json=submission_data)
    print(f"User 1 Submit Text Response: {response.status_code}, {response.text[:100]}...")
    assert response.status_code == 201 # Now expecting success
    submission1_response = response.json()
    submission1_id = submission1_response.get("id")
    assert submission1_id is not None
    print(f"User 1 Submitted Text ID: {submission1_id}")

    # i) List all submissions for the contest (user 1)
    # Based on api_roles_and_features.md, a regular user might not see submissions unless they are a judge or contest is closed/evaluation.
    # Let's test the endpoint but expect it might fail or return empty list depending on exact rules.
    print(f"User 1 Listing Submissions for Contest {contest1_id}...")
    response = requests.get(f"{BASE_URL}/contests/{contest1_id}/submissions", headers=headers_user1)
    print(f"User 1 List Submissions Response: {response.status_code}")
    # We cannot strongly assert the status code without knowing the exact permission logic.
    # If 403 Forbidden is expected for a user who is not a judge when contest is open, assert that.
    # If 200 OK with potentially filtered list (e.g., only own submissions) is expected, assert that.
    # Let's assume 403 Forbidden is the expected behavior for a non-judge viewing submissions in an open/private contest.
    assert response.status_code == 403 # Adjust based on actual API behavior
    # submissions = response.json()
    # print(f"User 1 List Submissions Count: {len(submissions)}")

    # j) Logout user 1 (No explicit logout endpoint needed, just stop using the token)
    print("User 1 workflow steps completed. Clearing token.")
    user1_token = None # Clear the token variable
    headers_user1 = {}

    # --- User 2 Workflow ---
    print("\n--- Starting User 2 Workflow ---")
    # k) Register new user 2
    user2_data = {"username": "usertest2", "email": "test2@user.plumas.top", "password": "12341324"}
    print(f"Registering User 2: {user2_data['username']}")
    response = requests.post(f"{BASE_URL}/auth/register", json=user2_data)
    print(f"User 2 Registration Response: {response.status_code}, {response.text[:100]}...")
    # Handle potential conflict if user already exists from previous failed run
    if response.status_code == 400 and 'already registered' in response.text.lower():
        print("User 2 already exists, proceeding to login.")
    else:
        assert response.status_code == 201

    # l) Login user 2
    login_data_2 = {"username": user2_data["username"], "password": user2_data["password"]}
    print(f"Logging in User 2: {user2_data['username']} (using username)")
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data_2) # Sending username, not email
    print(f"User 2 Login Response: {response.status_code}")
    assert response.status_code == 200
    user2_token = response.json().get("access_token")
    assert user2_token is not None
    print(f"User 2 Login Token obtained: {user2_token[:10]}...")
    headers_user2 = get_auth_headers(user2_token)

    # Get User 2 ID
    response = requests.get(f"{BASE_URL}/auth/users/me", headers=headers_user2)
    print(f"Get User 2 Info Response: {response.status_code}")
    assert response.status_code == 200
    user2_id = response.json().get("id")
    assert user2_id is not None
    print(f"User 2 ID: {user2_id}")

    #    c2) List all contests (user 2)
    print("User 2 Listing Contests...")
    response = requests.get(f"{BASE_URL}/contests/", headers=headers_user2)
    print(f"User 2 List Contests Response: {response.status_code}")
    assert response.status_code == 200
    # Optionally compare contest list length to initial_contests + 1

    #    d2) Create a new public contest (user 2)
    contest_data_2 = {
        "title": "User2 Test Contest E2E",
        "description": "Public contest created by user 2 for E2E testing.",
        "is_public": True
    }
    print(f"User 2 Creating Contest: {contest_data_2['title']}")
    response = requests.post(f"{BASE_URL}/contests/", headers=headers_user2, json=contest_data_2)
    print(f"User 2 Create Contest Response: {response.status_code}, {response.text[:100]}...")
    # Handle potential conflict if contest already exists from previous failed run
    if response.status_code == 400: # Or whatever code indicates conflict
         print(f"Conflict creating contest {contest_data_2['title']}, perhaps it exists. Trying to find it.")
         # Attempt to find the contest ID by listing and filtering
         list_resp = requests.get(f"{BASE_URL}/contests/", headers=headers_user2)
         if list_resp.status_code == 200:
             all_contests = list_resp.json()
             found = False
             for contest in all_contests:
                 if contest.get('title') == contest_data_2['title'] and contest.get('owner_id') == user2_id: # Check owner if possible
                     contest2_id = contest.get('id')
                     print(f"Found existing Contest ID for User 2: {contest2_id}")
                     found = True
                     break
             if not found:
                 pytest.fail("Failed to create or find existing contest for User 2")
         else:
              pytest.fail("Failed to list contests to find existing one for User 2")
    else:
        assert response.status_code == 201
        created_contest_2 = response.json()
        contest2_id = created_contest_2.get("id")
        assert contest2_id is not None
        print(f"User 2 Created Contest ID: {contest2_id}")


    #    e2) Modify the contest to private with password (user 2)
    update_data_2 = {
        "title": "User2 Test Contest E2E (Private)",
        "description": "User 2 Updated description, now private.",
        "contest_type": "private",
        "password": "asdfgh" # Different password for user 2's contest, >= 6 chars
    }
    print(f"User 2 Updating Contest {contest2_id} to Private...")
    response = requests.put(f"{BASE_URL}/contests/{contest2_id}", headers=headers_user2, json=update_data_2)
    print(f"User 2 Update Contest Response: {response.status_code}")
    assert response.status_code == 200

    #    f2) Check password with wrong password (user 2)
    check_pass_data_2 = {"password": "wrongpassword"}
    print(f"User 2 Checking Wrong Password for Contest {contest2_id}...")
    response = requests.post(f"{BASE_URL}/contests/{contest2_id}/check-password", headers=headers_user2, json=check_pass_data_2)
    print(f"User 2 Check Wrong Password Response: {response.status_code}")
    assert response.status_code == 403 # Changed from 401 based on current API code

    #    g2) Check password with correct password (user 2)
    check_pass_data_2 = {"password": "asdfgh"}
    print(f"User 2 Checking Correct Password for Contest {contest2_id}...")
    response_g2 = requests.post(f"{BASE_URL}/contests/{contest2_id}/check-password", headers=headers_user2, json=check_pass_data_2)
    print(f"User 2 Check Correct Password Response: {response_g2.status_code}, {response_g2.text[:100]}...")
    assert response_g2.status_code == 200
    # Capture the access cookie set by the response
    contest_access_cookie_2 = response_g2.cookies.get(f"contest_access_{contest2_id}")
    assert contest_access_cookie_2 is not None, f"Contest access cookie for {contest2_id} not found in response."
    print(f"User 2 Obtained Contest Access Cookie: {contest_access_cookie_2[:10]}...")

    # Add the cookie to subsequent requests for this contest
    headers_user2_with_cookie = headers_user2.copy()
    headers_user2_with_cookie['Cookie'] = f"contest_access_{contest2_id}={contest_access_cookie_2}"

    #    h2) Submit a text to the contest (user 2)
    submission_data_2 = {
        "title": "User2 Submission Title E2E",
        "text_content": "## Test Submission E2E by User 2\n\nThis is the content submitted by User 2."
    }
    print(f"User 2 Submitting Text to Contest {contest2_id}...")
    # Use headers WITH the contest access cookie
    response = requests.post(f"{BASE_URL}/contests/{contest2_id}/submissions", headers=headers_user2_with_cookie, json=submission_data_2)
    print(f"User 2 Submit Text Response: {response.status_code}, {response.text[:100]}...")
    # Handle potential conflict if submission already exists from previous failed run (less likely but possible)
    if response.status_code == 400: # Adjust error code as needed
        print(f"Conflict submitting to contest {contest2_id}. Checking if submission exists...")
        # We might need admin privileges or specific GET endpoint to find submission ID here
        # For now, assume test needs clean state or handle specific error
        pytest.skip(f"Skipping submission assertion due to potential existing submission for contest {contest2_id}")
    else:
        assert response.status_code == 201
        submission2_response = response.json()
        submission2_id = submission2_response.get("id")
        assert submission2_id is not None
        print(f"User 2 Submitted Text ID: {submission2_id}")

    #    i2) List all submissions for the contest (user 2)
    print(f"User 2 Listing Submissions for Contest {contest2_id}...")
    response = requests.get(f"{BASE_URL}/contests/{contest2_id}/submissions", headers=headers_user2)
    print(f"User 2 List Submissions Response: {response.status_code}")
    assert response.status_code == 403 # Assuming same logic as user 1

    # m) Try to delete contest 1 (created by user 1) - Expected failure
    assert contest1_id is not None # Ensure contest1_id was set
    print(f"User 2 Attempting to Delete Contest {contest1_id} (created by User 1)...")
    response = requests.delete(f"{BASE_URL}/contests/{contest1_id}", headers=headers_user2)
    print(f"User 2 Delete Contest 1 Response: {response.status_code}")
    assert response.status_code == 403 # Forbidden

    # n) Logout user 2 (Implicitly handled)
    print("User 2 workflow steps completed. Clearing token.")
    user2_token = None
    # headers_user2 = {} # Keep user2_data for admin deletion later

    # --- Cleanup ---
    print("\n--- Starting Cleanup Workflow ---")
    # o) Login user 1 again
    login_data_1_again = {"username": user1_data["username"], "password": user1_data["password"]}
    print(f"Re-logging in User 1: {user1_data['username']} (using username)")
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data_1_again) # Sending username, not email
    print(f"User 1 Re-Login Response: {response.status_code}")
    # If login fails (e.g., user already deleted by previous failed run), skip user cleanup steps
    if response.status_code != 200:
         print("User 1 re-login failed, possibly already deleted. Skipping User 1 cleanup.")
         headers_user1 = {} # Ensure no stale headers
    else:
        user1_token = response.json().get("access_token")
        assert user1_token is not None
        print(f"User 1 Re-Login Token obtained: {user1_token[:10]}...")
        headers_user1 = get_auth_headers(user1_token)

        #    o1) Delete contest 1 (user 1)
        assert contest1_id is not None
        print(f"User 1 Deleting Contest {contest1_id}...")
        response = requests.delete(f"{BASE_URL}/contests/{contest1_id}", headers=headers_user1)
        print(f"User 1 Delete Contest 1 Response: {response.status_code}")
        # Allow 404 Not Found if already deleted
        assert response.status_code in [200, 204, 404]

        #    o2) Try to delete contest 2 (user 1) - Expected failure
        assert contest2_id is not None
        print(f"User 1 Attempting to Delete Contest {contest2_id} (created by User 2)...")
        response = requests.delete(f"{BASE_URL}/contests/{contest2_id}", headers=headers_user1)
        print(f"User 1 Delete Contest 2 Response: {response.status_code}")
        assert response.status_code == 403 # Forbidden

    # p) Login as admin
    assert ADMIN_USERNAME and ADMIN_PASSWORD, "Admin credentials not found in .env file"
    admin_login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    print(f"Logging in as Admin: {ADMIN_USERNAME} (using username)")
    response = requests.post(f"{BASE_URL}/auth/token", data=admin_login_data) # Sending username from .env
    print(f"Admin Login Response: {response.status_code}")
    assert response.status_code == 200
    admin_token = response.json().get("access_token")
    assert admin_token is not None
    headers_admin = get_auth_headers(admin_token)
    print("Admin Login Successful.")

    #    p1) Delete user 1
    #    NOTE: api_roles_and_features.md shows '[ ] Delete User' under Admin.
    #    Assuming endpoint DELETE /admin/users/{user_id} for testing purposes. Adjust if different.
    if user1_id:
        print(f"Admin Deleting User 1 (ID: {user1_id})...")
        response = requests.delete(f"{BASE_URL}/admin/users/{user1_id}", headers=headers_admin)
        print(f"Admin Delete User 1 Response: {response.status_code}")
        # Allow 404 Not Found if user was already deleted or login failed earlier
        assert response.status_code in [204]
    else:
        print("Skipping Admin Delete User 1 (ID not available).")


    #    p2) Delete user 2
    if user2_id:
        print(f"Admin Deleting User 2 (ID: {user2_id})...")
        response = requests.delete(f"{BASE_URL}/admin/users/{user2_id}", headers=headers_admin)
        print(f"Admin Delete User 2 Response: {response.status_code}")
        # Allow 404 Not Found
        assert response.status_code in [204]
    else:
        print("Skipping Admin Delete User 2 (ID not available).")

    #    p3) Delete contest 2 (admin)
    #    NOTE: api_roles_and_features.md shows '[x] Delete Any Contest (DELETE /contests/{contest_id})'
    if contest2_id:
        print(f"Admin Deleting Contest 2 (ID: {contest2_id})...")
        response = requests.delete(f"{BASE_URL}/contests/{contest2_id}", headers=headers_admin)
        print(f"Admin Delete Contest 2 Response: {response.status_code}")
        # Allow 404 Not Found
        assert response.status_code in [404]
    else:
        print("Skipping Admin Delete Contest 2 (ID not available).")


    print("\n--- E2E Test Cleanup Completed ---")

# Consider using pytest fixtures for setup/teardown for more robust cleanup
# e.g., register users/create contests in setup, delete in teardown

# Add try...finally block? Or rely on pytest fixtures for cleanup?
# For simplicity now, direct cleanup steps are included in the test. 