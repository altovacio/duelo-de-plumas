import requests
import pytest
import os
from dotenv import load_dotenv
import time # Import time for potential delays/retries if needed

# Load environment variables from .env file
load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # Default if not set
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Helper function to get auth headers
def get_auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

# Helper function to register a user, handles conflicts
def register_user(username, email, password):
    user_data = {"username": username, "email": email, "password": password}
    print(f"Registering User: {username}")
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Registration Response ({username}): {response.status_code}, {response.text[:100]}...")
    if response.status_code == 400 and (
        'already registered' in response.text.lower() or
        'user with this email already exists' in response.text.lower() or
        'user with this username already exists' in response.text.lower()
    ):
        print(f"User {username} already exists, proceeding.")
        return False # Indicate user already existed
    elif response.status_code == 201:
        print(f"User {username} registered successfully.")
        return True # Indicate successful registration
    else:
        pytest.fail(f"User {username} registration failed unexpectedly: {response.status_code} - {response.text}")

# Helper function to login and get token/ID
def login_user(username, password):
    login_data = {"username": username, "password": password}
    print(f"Logging in User: {username}")
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    print(f"Login Response ({username}): {response.status_code}")
    if response.status_code != 200:
         pytest.fail(f"Login failed for user {username}: {response.status_code} - {response.text}")
    token = response.json().get("access_token")
    assert token is not None, f"Failed to get token for user {username}"
    print(f"Login Token obtained ({username}): {token[:10]}...")
    headers = get_auth_headers(token)

    # Get User ID
    response_me = requests.get(f"{BASE_URL}/auth/users/me", headers=headers)
    print(f"Get User Info Response ({username}): {response_me.status_code}")
    assert response_me.status_code == 200
    user_id = response_me.json().get("id")
    assert user_id is not None, f"Failed to get ID for user {username}"
    print(f"User ID ({username}): {user_id}")
    return token, user_id

@pytest.mark.e2e
def test_ai_agent_user_admin_workflow():
    """Runs an end-to-end workflow test for User-Owned AI Agents.

    Covers CRUD operations for AI Writers and Judges by their owners,
    checks access restrictions between users, and verifies admin capabilities
    including modification and deletion of user agents, and cascading deletes upon user removal.

    **Assumptions:**
    - User-specific endpoints like `/users/me/ai-writers`, `/users/me/ai-judges` exist for CRUD.
    - Admin endpoints `/admin/ai-writers`, `/admin/ai-judges` exist for listing, viewing, updating, and deleting ANY agent.
    - Deleting a user via `/admin/users/{user_id}` cascades and deletes all associated agents, contests, submissions, etc.
    - AI Action Request/Approval endpoints are currently out of scope ([ ] in spec).

    **Steps:**

    --- Setup ---
    1.  Register User 1 (`ai_user1`)
    2.  Login User 1 & Get ID
    3.  Register User 2 (`ai_user2`)
    4.  Login User 2 & Get ID
    5.  Login Admin

    --- User 1 AI Writer Workflow ---
    a)  List Own AI Writers (User 1 - Expect empty)
    b)  Create AI Writer (User 1 - `writer1`)
    c)  List Own AI Writers (User 1 - Expect `writer1`)
    d)  View Own AI Writer Details (User 1 - `writer1`)
    e)  Update Own AI Writer (User 1 - `writer1`)
    f)  View Updated AI Writer Details (User 1 - `writer1`)
    g)  *Future: Request AI Writer Action (User 1 - `writer1`)*

    --- User 2 AI Writer Checks ---
    h)  List Own AI Writers (User 2 - Expect empty)
    i)  Try View User 1's AI Writer (User 2 - `writer1` - Expect 403/404)
    j)  Try Update User 1's AI Writer (User 2 - `writer1` - Expect 403/404)
    k)  Create AI Writer (User 2 - `writer2`)
    l)  List Own AI Writers (User 2 - Expect `writer2`)
    m)  Try Delete User 1's AI Writer (User 2 - `writer1` - Expect 403/404)

    --- User 1 AI Judge Workflow ---
    n)  List Own AI Judges (User 1 - Expect empty)
    o)  Create AI Judge (User 1 - `judge1`)
    p)  List Own AI Judges (User 1 - Expect `judge1`)
    q)  View Own AI Judge Details (User 1 - `judge1`)
    r)  Update Own AI Judge (User 1 - `judge1`)
    s)  View Updated AI Judge Details (User 1 - `judge1`)
    t)  *Future: Request AI Judge Action (User 1 - `judge1`)*

    --- User 2 AI Judge Checks ---
    u)  List Own AI Judges (User 2 - Expect empty)
    v)  Try View User 1's AI Judge (User 2 - `judge1` - Expect 403/404)
    w)  Try Update User 1's AI Judge (User 2 - `judge1` - Expect 403/404)
    x)  Create AI Judge (User 2 - `judge2`)
    y)  List Own AI Judges (User 2 - Expect `judge2`)
    z)  Try Delete User 1's AI Judge (User 2 - `judge1` - Expect 403/404)

    --- Admin AI Checks & Management ---
    aa) List All AI Writers (Admin - Check `writer1`, `writer2` appear via `/admin/ai-writers`)
    ab) List All AI Judges (Admin - Check `judge1`, `judge2` appear via `/admin/ai-judges`)
    ac) View User 1's AI Writer Details (Admin - `writer1` - Expect success via admin endpoint)
    ad) View User 2's AI Judge Details (Admin - `judge2` - Expect success via admin endpoint)
    ae) Update User 1's AI Writer (Admin - `writer1` - Expect success 200)
    af) Update User 2's AI Judge (Admin - `judge2` - Expect success 200)
    ag) *Future: List User AI Action Requests (Admin)*
    ah) *Future: Approve/Reject User 1's Writer Request (Admin)*
    ai) *Future: Approve/Reject User 1's Judge Request (Admin)*
    aj) Delete User 1's AI Writer (Admin - `writer1` - Expect success via `/admin/ai-writers/{id}`)
    ak) Delete User 2's AI Judge (Admin - `judge2` - Expect success via `/admin/ai-judges/{id}`)

    --- User 1 Final Checks ---
    al) List Own AI Writers (User 1 - Expect empty as deleted by admin `aj`)
    am) Try View Deleted AI Writer (User 1 - `writer1` - Expect 404)
    an) Delete Own AI Judge (User 1 - `judge1` - Expect success)
    ao) List Own AI Judges (User 1 - Expect empty)

    --- User 2 Final Checks (Before User Deletion) ---
    ap) List Own AI Writers (User 2 - Expect `writer2`)
    aq) Delete Own AI Writer (User 2 - `writer2` - Expect success)
    ar) List Own AI Writers (User 2 - Expect empty)
    as) List Own AI Judges (User 2 - Expect empty as deleted by admin `ak`)
    at) Try View Deleted AI Judge (User 2 - `judge2` - Expect 404)

    --- Cleanup & Verification ---
    au) Delete User 1 (Admin)
    av) Verify User 1's Judge deleted (Admin try Get `/admin/ai-judges/{user1_judge_id}` - Expect 404)
    aw) Delete User 2 (Admin)
    ax) Verify User 2's Writer deleted (Admin try Get `/admin/ai-writers/{user2_writer_id}` - Expect 404, due to cascade delete)
    ay) Verify User 2's Judge deleted (Admin try Get `/admin/ai-judges/{user2_judge_id}` - Expect 404, already deleted in `ak`)
    az) List All AI Writers (Admin - Expect empty or only admin-owned)
    ba) List All AI Judges (Admin - Expect empty or only admin-owned)
    bb) *Optional: Delete any remaining Admin-owned agents created during test*
    """
    user1_token = None
    user1_id = None
    user2_token = None
    user2_id = None
    admin_token = None

    user1_writer_id = None
    user1_judge_id = None
    user2_writer_id = None
    user2_judge_id = None

    # Use unique usernames/emails for each test run
    timestamp = int(time.time())
    user1_username = f"ai_user1_e2e_{timestamp}"
    user1_email = f"ai_user1_{timestamp}@test.e2e"
    user1_password = "password123"

    user2_username = f"ai_user2_e2e_{timestamp}"
    user2_email = f"ai_user2_{timestamp}@test.e2e"
    user2_password = "password456"
    
    print(f"\n--- Running AI Agent E2E Test against {BASE_URL} ---")

    # --- Setup ---
    print("\n--- Setup: Registering/Logging in Users & Admin ---")
    # 1. Register User 1
    register_user(user1_username, user1_email, user1_password)
    # 2. Login User 1 & Get ID
    user1_token, user1_id = login_user(user1_username, user1_password)
    headers_user1 = get_auth_headers(user1_token)

    # 3. Register User 2
    register_user(user2_username, user2_email, user2_password)
    # 4. Login User 2 & Get ID
    user2_token, user2_id = login_user(user2_username, user2_password)
    headers_user2 = get_auth_headers(user2_token)

    # 5. Login Admin
    admin_token, _ = login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
    headers_admin = get_auth_headers(admin_token)
    print("Setup Complete.")

    try: # Wrap test steps in try...finally for cleanup
        # --- User 1 AI Writer Workflow ---
        print("\n--- User 1 AI Writer Workflow ---")
        # a) List Own AI Writers (User 1 - Expect empty)
        print("User 1: Listing initial AI Writers...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user1)
        print(f"User 1 List Writers (Initial): {response.status_code}, {response.text[:100]}...")
        assert response.status_code == 200
        assert response.json() == []

        # b) Create AI Writer (User 1 - `writer1`)
        writer1_data = {
            "name": f"User1 Writer Alpha E2E {timestamp}", # Ensure unique name
            "description": "First AI writer for User 1.",
            "personality_prompt": "You are Alpha, a concise writer."
        }
        print(f"User 1: Creating AI Writer '{writer1_data['name']}'...")
        response = requests.post(f"{BASE_URL}/ai-writers/", headers=headers_user1, json=writer1_data)
        print(f"User 1 Create Writer Response: {response.status_code}, {response.text[:100]}...")
        assert response.status_code == 201
        writer1_details = response.json()
        user1_writer_id = writer1_details.get("id")
        assert user1_writer_id is not None
        print(f"User 1 Created Writer ID: {user1_writer_id}")

        # c) List Own AI Writers (User 1 - Expect `writer1`)
        print("User 1: Listing AI Writers again...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user1)
        print(f"User 1 List Writers (Post-Create): {response.status_code}")
        assert response.status_code == 200
        writers_list = response.json()
        assert len(writers_list) == 1
        assert writers_list[0]["id"] == user1_writer_id
        assert writers_list[0]["name"] == writer1_data["name"]

        # d) View Own AI Writer Details (User 1 - `writer1`)
        print(f"User 1: Viewing AI Writer {user1_writer_id} details...")
        response = requests.get(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user1)
        print(f"User 1 View Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 200
        details = response.json()
        assert details["id"] == user1_writer_id
        assert details["name"] == writer1_data["name"]
        assert details["owner_id"] == user1_id

        # e) Update Own AI Writer (User 1 - `writer1`)
        writer1_update_data = {
            "name": f"User1 Writer Alpha E2E {timestamp} (Updated)",
            "description": "Updated description.",
        }
        print(f"User 1: Updating AI Writer {user1_writer_id}...")
        response = requests.put(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user1, json=writer1_update_data)
        print(f"User 1 Update Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 200
        updated_details = response.json()
        assert updated_details["name"] == writer1_update_data["name"]
        assert updated_details["description"] == writer1_update_data["description"]

        # f) View Updated AI Writer Details (User 1 - `writer1`)
        print(f"User 1: Viewing updated AI Writer {user1_writer_id} details...")
        response = requests.get(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user1)
        print(f"User 1 View Updated Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 200
        details = response.json()
        assert details["id"] == user1_writer_id
        assert details["name"] == writer1_update_data["name"]

        # g) Future: Request AI Writer Action - Skipped

        # --- User 2 AI Writer Checks ---
        print("\n--- User 2 AI Writer Checks ---")
        # h) List Own AI Writers (User 2 - Expect empty)
        print("User 2: Listing initial AI Writers...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user2)
        print(f"User 2 List Writers (Initial): {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # i) Try View User 1's AI Writer (User 2 - Expect 403)
        print(f"User 2: Attempting to view User 1's Writer {user1_writer_id}...")
        response = requests.get(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user2)
        print(f"User 2 View User 1 Writer Response: {response.status_code}")
        assert response.status_code == 403 # Forbidden

        # j) Try Update User 1's AI Writer (User 2 - Expect 403)
        print(f"User 2: Attempting to update User 1's Writer {user1_writer_id}...")
        response = requests.put(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user2, json={"description": "User 2 trying to update"})
        print(f"User 2 Update User 1 Writer Response: {response.status_code}")
        assert response.status_code == 403 # Forbidden

        # k) Create AI Writer (User 2 - `writer2`)
        writer2_data = {
            "name": f"User2 Writer Beta E2E {timestamp}", # Unique name
            "description": "AI writer for User 2.",
            "personality_prompt": "You are Beta, an elaborate writer."
        }
        print(f"User 2: Creating AI Writer '{writer2_data['name']}'...")
        response = requests.post(f"{BASE_URL}/ai-writers/", headers=headers_user2, json=writer2_data)
        print(f"User 2 Create Writer Response: {response.status_code}, {response.text[:100]}...")
        assert response.status_code == 201
        writer2_details = response.json()
        user2_writer_id = writer2_details.get("id")
        assert user2_writer_id is not None
        print(f"User 2 Created Writer ID: {user2_writer_id}")

        # l) List Own AI Writers (User 2 - Expect `writer2`)
        print("User 2: Listing AI Writers again...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user2)
        print(f"User 2 List Writers (Post-Create): {response.status_code}")
        assert response.status_code == 200
        writers_list = response.json()
        assert len(writers_list) == 1
        assert writers_list[0]["id"] == user2_writer_id
        assert writers_list[0]["name"] == writer2_data["name"]

        # m) Try Delete User 1's AI Writer (User 2 - Expect 403)
        print(f"User 2: Attempting to delete User 1's Writer {user1_writer_id}...")
        response = requests.delete(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user2)
        print(f"User 2 Delete User 1 Writer Response: {response.status_code}")
        assert response.status_code == 403 # Forbidden

        # --- User 1 AI Judge Workflow ---
        print("\n--- User 1 AI Judge Workflow ---")
        # n) List Own AI Judges (User 1 - Expect empty)
        print("User 1: Listing initial AI Judges...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user1)
        print(f"User 1 List Judges (Initial): {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # o) Create AI Judge (User 1 - `judge1`)
        judge1_data = {
            "name": f"User1 Judge Omega E2E {timestamp}", # Unique name
            "description": "First AI judge for User 1.",
            "personality_prompt": "You are Omega, a fair judge."
        }
        print(f"User 1: Creating AI Judge '{judge1_data['name']}'...")
        response = requests.post(f"{BASE_URL}/ai-judges/", headers=headers_user1, json=judge1_data)
        print(f"User 1 Create Judge Response: {response.status_code}, {response.text[:100]}...")
        assert response.status_code == 201
        judge1_details = response.json()
        user1_judge_id = judge1_details.get("id")
        assert user1_judge_id is not None
        print(f"User 1 Created Judge ID: {user1_judge_id}")

        # p) List Own AI Judges (User 1 - Expect `judge1`)
        print("User 1: Listing AI Judges again...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user1)
        print(f"User 1 List Judges (Post-Create): {response.status_code}")
        assert response.status_code == 200
        judges_list = response.json()
        assert len(judges_list) == 1
        assert judges_list[0]["id"] == user1_judge_id

        # q) View Own AI Judge Details (User 1 - `judge1`)
        print(f"User 1: Viewing AI Judge {user1_judge_id} details...")
        response = requests.get(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user1)
        print(f"User 1 View Judge {user1_judge_id} Response: {response.status_code}")
        assert response.status_code == 200
        details = response.json()
        assert details["id"] == user1_judge_id
        assert details["owner_id"] == user1_id

        # r) Update Own AI Judge (User 1 - `judge1`)
        judge1_update_data = {"name": f"User1 Judge Omega E2E {timestamp} (Updated)"}
        print(f"User 1: Updating AI Judge {user1_judge_id}...")
        response = requests.put(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user1, json=judge1_update_data)
        print(f"User 1 Update Judge {user1_judge_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["name"] == judge1_update_data["name"]

        # s) View Updated AI Judge Details (User 1 - `judge1`)
        print(f"User 1: Viewing updated AI Judge {user1_judge_id} details...")
        response = requests.get(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user1)
        print(f"User 1 View Updated Judge {user1_judge_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["name"] == judge1_update_data["name"]

        # t) Future: Request AI Judge Action - Skipped

        # --- User 2 AI Judge Checks ---
        print("\n--- User 2 AI Judge Checks ---")
        # u) List Own AI Judges (User 2 - Expect empty)
        print("User 2: Listing initial AI Judges...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user2)
        print(f"User 2 List Judges (Initial): {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # v) Try View User 1's AI Judge (User 2 - Expect 403)
        print(f"User 2: Attempting to view User 1's Judge {user1_judge_id}...")
        response = requests.get(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user2)
        print(f"User 2 View User 1 Judge Response: {response.status_code}")
        assert response.status_code == 403

        # w) Try Update User 1's AI Judge (User 2 - Expect 403)
        print(f"User 2: Attempting to update User 1's Judge {user1_judge_id}...")
        response = requests.put(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user2, json={"description": "User 2 trying to update"})
        print(f"User 2 Update User 1 Judge Response: {response.status_code}")
        assert response.status_code == 403

        # x) Create AI Judge (User 2 - `judge2`)
        judge2_data = {
            "name": f"User2 Judge Sigma E2E {timestamp}", # Unique name
            "description": "AI judge for User 2.",
            "personality_prompt": "You are Sigma, a strict judge."
        }
        print(f"User 2: Creating AI Judge '{judge2_data['name']}'...")
        response = requests.post(f"{BASE_URL}/ai-judges/", headers=headers_user2, json=judge2_data)
        print(f"User 2 Create Judge Response: {response.status_code}, {response.text[:100]}...")
        assert response.status_code == 201
        judge2_details = response.json()
        user2_judge_id = judge2_details.get("id")
        assert user2_judge_id is not None
        print(f"User 2 Created Judge ID: {user2_judge_id}")

        # y) List Own AI Judges (User 2 - Expect `judge2`)
        print("User 2: Listing AI Judges again...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user2)
        print(f"User 2 List Judges (Post-Create): {response.status_code}")
        assert response.status_code == 200
        judges_list = response.json()
        assert len(judges_list) == 1
        assert judges_list[0]["id"] == user2_judge_id

        # z) Try Delete User 1's AI Judge (User 2 - Expect 403)
        print(f"User 2: Attempting to delete User 1's Judge {user1_judge_id}...")
        response = requests.delete(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user2)
        print(f"User 2 Delete User 1 Judge Response: {response.status_code}")
        assert response.status_code == 403

        # --- Admin AI Checks & Management ---
        print("\n--- Admin AI Checks & Management ---")
        # aa) List All AI Writers (Admin)
        print("Admin: Listing all AI Writers...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_admin)
        print(f"Admin List All Writers Response: {response.status_code}")
        assert response.status_code == 200
        all_writers = response.json()
        all_writer_ids = [w["id"] for w in all_writers]
        assert user1_writer_id in all_writer_ids
        assert user2_writer_id in all_writer_ids
        print(f"Admin found writers, including {user1_writer_id} and {user2_writer_id}")

        # ab) List All AI Judges (Admin)
        print("Admin: Listing all AI Judges...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_admin)
        print(f"Admin List All Judges Response: {response.status_code}")
        assert response.status_code == 200
        all_judges = response.json()
        all_judge_ids = [j["id"] for j in all_judges]
        assert user1_judge_id in all_judge_ids
        assert user2_judge_id in all_judge_ids
        print(f"Admin found judges, including {user1_judge_id} and {user2_judge_id}")

        # ac) View User 1's AI Writer Details (Admin)
        print(f"Admin: Viewing User 1's Writer {user1_writer_id}...")
        response = requests.get(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_admin)
        print(f"Admin View User 1 Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["owner_id"] == user1_id

        # ad) View User 2's AI Judge Details (Admin)
        print(f"Admin: Viewing User 2's Judge {user2_judge_id}...")
        response = requests.get(f"{BASE_URL}/ai-judges/{user2_judge_id}", headers=headers_admin)
        print(f"Admin View User 2 Judge {user2_judge_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["owner_id"] == user2_id

        # ae) Update User 1's AI Writer (Admin)
        admin_writer_update = {"description": "Admin updated description."}
        print(f"Admin: Updating User 1's Writer {user1_writer_id}...")
        response = requests.put(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_admin, json=admin_writer_update)
        print(f"Admin Update User 1 Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["description"] == admin_writer_update["description"]

        # af) Update User 2's AI Judge (Admin)
        admin_judge_update = {"description": "Admin updated judge description."}
        print(f"Admin: Updating User 2's Judge {user2_judge_id}...")
        response = requests.put(f"{BASE_URL}/ai-judges/{user2_judge_id}", headers=headers_admin, json=admin_judge_update)
        print(f"Admin Update User 2 Judge {user2_judge_id} Response: {response.status_code}")
        assert response.status_code == 200
        assert response.json()["description"] == admin_judge_update["description"]

        # ag-ai) Future AI Action Requests - Skipped

        # aj) Delete User 1's AI Writer (Admin)
        print(f"Admin: Deleting User 1's Writer {user1_writer_id}...")
        response = requests.delete(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_admin)
        print(f"Admin Delete User 1 Writer {user1_writer_id} Response: {response.status_code}")
        assert response.status_code == 204

        # ak) Delete User 2's AI Judge (Admin)
        print(f"Admin: Deleting User 2's Judge {user2_judge_id}...")
        response = requests.delete(f"{BASE_URL}/ai-judges/{user2_judge_id}", headers=headers_admin)
        print(f"Admin Delete User 2 Judge {user2_judge_id} Response: {response.status_code}")
        assert response.status_code == 204

        # --- User 1 Final Checks ---
        print("\n--- User 1 Final Checks ---")
        # al) List Own AI Writers (Expect empty)
        print("User 1: Listing AI Writers (expect empty after admin delete)...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user1)
        print(f"User 1 List Writers Final: {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # am) Try View Deleted AI Writer (Expect 404)
        print(f"User 1: Attempting to view deleted Writer {user1_writer_id}...")
        response = requests.get(f"{BASE_URL}/ai-writers/{user1_writer_id}", headers=headers_user1)
        print(f"User 1 View Deleted Writer Response: {response.status_code}")
        assert response.status_code == 404

        # an) Delete Own AI Judge (Expect success)
        print(f"User 1: Deleting own Judge {user1_judge_id}...")
        response = requests.delete(f"{BASE_URL}/ai-judges/{user1_judge_id}", headers=headers_user1)
        print(f"User 1 Delete Own Judge Response: {response.status_code}")
        assert response.status_code == 204

        # ao) List Own AI Judges (Expect empty)
        print("User 1: Listing AI Judges (expect empty after self delete)...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user1)
        print(f"User 1 List Judges Final: {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # --- User 2 Final Checks ---
        print("\n--- User 2 Final Checks ---")
        # ap) List Own AI Writers (Expect `writer2`)
        print("User 2: Listing AI Writers (expect writer2)...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user2)
        print(f"User 2 List Writers (Before Delete): {response.status_code}")
        assert response.status_code == 200
        writers_list = response.json()
        assert len(writers_list) == 1
        assert writers_list[0]["id"] == user2_writer_id

        # aq) Delete Own AI Writer (Expect success)
        print(f"User 2: Deleting own Writer {user2_writer_id}...")
        response = requests.delete(f"{BASE_URL}/ai-writers/{user2_writer_id}", headers=headers_user2)
        print(f"User 2 Delete Own Writer Response: {response.status_code}")
        assert response.status_code == 204

        # ar) List Own AI Writers (Expect empty)
        print("User 2: Listing AI Writers (expect empty after self delete)...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_user2)
        print(f"User 2 List Writers Final: {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # as) List Own AI Judges (Expect empty)
        print("User 2: Listing AI Judges (expect empty after admin delete)...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_user2)
        print(f"User 2 List Judges Final: {response.status_code}")
        assert response.status_code == 200
        assert response.json() == []

        # at) Try View Deleted AI Judge (Expect 404)
        print(f"User 2: Attempting to view deleted Judge {user2_judge_id}...")
        response = requests.get(f"{BASE_URL}/ai-judges/{user2_judge_id}", headers=headers_user2)
        print(f"User 2 View Deleted Judge Response: {response.status_code}")
        assert response.status_code == 404

        print("\n--- Main Test Steps Completed ---")

    finally:
        # --- Cleanup & Verification ---
        print("\n--- Final Cleanup & Verification (Admin Actions) ---")
        # Re-login admin just in case token expired
        try:
             admin_token, _ = login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
             headers_admin = get_auth_headers(admin_token)
        except Exception as e:
             print(f"WARN: Admin re-login failed during cleanup: {e}")
             if not admin_token:
                 pytest.fail("Admin re-login failed, cannot clean up test users.")

        # Robust cleanup: Delete agents directly first, then users
        print("Admin: Attempting direct cleanup of any remaining test agents...")
        agent_endpoints = [
            (user1_writer_id, "/ai-writers"), (user2_writer_id, "/ai-writers"),
            (user1_judge_id, "/ai-judges"), (user2_judge_id, "/ai-judges")
        ]
        for agent_id, endpoint_prefix in agent_endpoints:
            if agent_id:
                 response = requests.delete(f"{BASE_URL}{endpoint_prefix}/{agent_id}", headers=headers_admin)
                 print(f"Admin cleanup delete {endpoint_prefix}/{agent_id}: {response.status_code}")
                 # We expect 404 if already deleted, 204 if successful now
                 assert response.status_code in [204, 404]

        # au) Delete User 1 (Admin)
        if user1_id:
            print(f"Admin: Deleting User 1 (ID: {user1_id}) via Admin endpoint...")
            response = requests.delete(f"{BASE_URL}/admin/users/{user1_id}", headers=headers_admin)
            print(f"Admin Delete User 1 Response: {response.status_code}")
            assert response.status_code in [204, 404]
        else:
            print("Skipping Admin Delete User 1 (ID not available).")

        # aw) Delete User 2 (Admin)
        if user2_id:
            print(f"Admin: Deleting User 2 (ID: {user2_id}) via Admin endpoint...")
            response = requests.delete(f"{BASE_URL}/admin/users/{user2_id}", headers=headers_admin)
            print(f"Admin Delete User 2 Response: {response.status_code}")
            assert response.status_code in [204, 404]
        else:
            print("Skipping Admin Delete User 2 (ID not available).")
            
        # av, ax, ay) Verify deletions via GET (expect 404) - Should be redundant if delete user cascades
        # Let's keep these checks for robustness
        print("Admin: Verifying agent deletions via GET requests...")
        for agent_id, endpoint_prefix in agent_endpoints:
            if agent_id:
                 verify_response = requests.get(f"{BASE_URL}{endpoint_prefix}/{agent_id}", headers=headers_admin)
                 print(f"Admin verify GET {endpoint_prefix}/{agent_id}: {verify_response.status_code}")
                 assert verify_response.status_code == 404

        # az) List All AI Writers (Admin - Final Check)
        print("Admin: Listing all AI Writers (final check)...")
        response = requests.get(f"{BASE_URL}/ai-writers/", headers=headers_admin)
        print(f"Admin List All Writers Final Response: {response.status_code}")
        assert response.status_code == 200
        final_writers = [w for w in response.json() if w.get('owner_id') in [user1_id, user2_id]]
        assert final_writers == [], f"Found unexpected user-owned writers during final cleanup: {final_writers}"
        print("Admin final writer list check passed.")

        # ba) List All AI Judges (Admin - Final Check)
        print("Admin: Listing all AI Judges (final check)...")
        response = requests.get(f"{BASE_URL}/ai-judges/", headers=headers_admin)
        print(f"Admin List All Judges Final Response: {response.status_code}")
        assert response.status_code == 200
        final_judges = [j for j in response.json() if j.get('owner_id') in [user1_id, user2_id]]
        assert final_judges == [], f"Found unexpected user-owned judges during final cleanup: {final_judges}"
        print("Admin final judge list check passed.")

        # bb) Optional: Delete admin agents - Skipped

        print("\n--- AI Agent E2E Test Cleanup Completed Successfully ---")

# Add helper functions for user registration, login, etc. as needed, similar to test_workflow_e2e.py 