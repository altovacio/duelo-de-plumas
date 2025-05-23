import requests
import json

BASE_URL = "http://localhost:8000"  # Adjusted based on api_endpoints_programmatically.md
# Check your main.py or where the root API router is mounted.
# If your endpoints are directly under /api/, then BASE_URL = "http://localhost:8000/api"
# If your endpoints are directly under / (e.g. /auth/login), then BASE_URL = "http://localhost:8000"


def print_response(response: requests.Response, action: str):
    """Helper function to print API call results."""
    print(f"--- {action} ---")
    try:
        print(f"Status Code: {response.status_code}")
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
        if response.status_code >= 400:
            print(f"ERROR: {action} failed.")
        return response_json
    except json.JSONDecodeError:
        print(f"Response (not JSON): {response.text}")
        if response.status_code >= 400:
            print(f"ERROR: {action} failed.")
        return None

# --- Authentication ---
def signup_user(username, email, password):
    payload = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    return print_response(response, f"Signup User: {username}")

def login_user(username, password):
    payload = {"username": username, "password": password} # FastAPI's OAuth2PasswordRequestForm uses 'username' for email
    response = requests.post(f"{BASE_URL}/auth/login", data=payload) # Login expects form data
    data = print_response(response, f"Login User: {username}")
    if data and "access_token" in data:
        return data["access_token"]
    return None

def assign_user_credits(token, user_id, credits):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"credits": credits, "description": 'admin_adjustment'}
    response = requests.post(f"{BASE_URL}/admin/users/{user_id}/credits", headers=headers, json=payload)
    return print_response(response, f"Assign Credits to User {user_id}")

# --- Generic Resource Creation ---
def create_contest_api(token, title, description, is_private, password=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "description": description,
        "is_private": is_private,
        "min_votes_required": 1, # Default
        # "end_date": None, # Optional, leave open
        # "judge_restrictions": {}, # Optional
        # "author_restrictions": {} # Optional
    }
    if is_private and password:
        payload["password"] = password
    
    response = requests.post(f"{BASE_URL}/contests/", headers=headers, json=payload)
    return print_response(response, f"Create Contest: {title}")

def create_text_api(token, title, content, author):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content, "author": author}
    response = requests.post(f"{BASE_URL}/texts/", headers=headers, json=payload)
    return print_response(response, f"Create Text: {title}")

def create_agent_api(token, name, description, agent_type, prompt, model="default_model_for_testing", is_public=False):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "description": description,
        "type": agent_type, # "writer" or "judge"
        "prompt": prompt,
        "model": model, 
        "is_public": is_public
    }
    response = requests.post(f"{BASE_URL}/agents/", headers=headers, json=payload)
    return print_response(response, f"Create Agent: {name} ({agent_type})")

# --- Main Script Logic ---
if __name__ == "__main__":
    print("Starting Duelo de Plumas Debug Init Script...")

    # --- Admin User Credentials (PLEASE VERIFY/ADJUST) ---
    ADMIN_USERNAME = "Hefesto"
    ADMIN_PASSWORD = "itaca" # Ensure this matches your actual admin password


    user4_token = login_user("user4", "123123")
    # Step a) Create user1 and user2
    print("\n=== Step A: Create Users ===")
    signup_user("user1", "user1@test.plumas.top", "123123")
    signup_user("user2", "user2@test.plumas.top", "321321")
    signup_user("user3", "user3@test.plumas.top", "123123")

    # Login users to get tokens
    print("\n=== Login Users ===")
    user1_token = login_user("user1", "123123")
    user2_token = login_user("user2", "321321")
    admin_token = login_user(ADMIN_USERNAME, ADMIN_PASSWORD)

    if not user1_token:
        print("ERROR: Could not log in user1. Halting script.")
        exit()
    if not user2_token:
        print("ERROR: Could not log in user2. Halting script.")
        exit()
    if not admin_token:
        print(f"WARNING: Could not log in admin ({ADMIN_USERNAME}). Admin actions will be skipped.")
        print("Ensure the admin user exists with the specified credentials or adjust ADMIN_USERNAME/ADMIN_PASSWORD.")

    # Step b) user1 creates a private contest
    if user1_token:
        print("\n=== Step B: User1 Creates Private Contest ===")
        create_contest_api(
            user1_token,
            title="User1 Private Test Contest",
            description="This is a private contest created by user1 for testing. Password is '1'.",
            is_private=True,
            password="1"
        )

    # Step c) user2 creates a public contest
    if user2_token:
        print("\n=== Step C: User2 Creates Public Contest ===")
        create_contest_api(
            user2_token,
            title="User2 Public Test Contest",
            description="This is a public contest created by user2 for testing.",
            is_private=False
        )

    # Step d) user1 and user2 each create a very simple text
    print("\n=== Step D: Users Create Texts ===")
    if user1_token:
        create_text_api(
            user1_token,
            title="User1's First Text",
            content="This is a very simple text written by user1.",
            author="user1-pseudonym" # Assuming author is username, adjust if schema differs
        )
        create_text_api(
            user1_token,
            title="User1's Second Text",
            content="This is the sequel to the first text written by user1.",
            author="user1-pseudonym" # Assuming author is username, adjust if schema differs
        )
        for i in range(10):
            create_text_api(
                user1_token,
                title=f"User1's Text {i+1} in a cycle",
                content=f"This is the {i+1}th text written by user1. "*50,
                author="user1-pseudonym" # Assuming author is username, adjust if schema differs
            )
    if user2_token:
        create_text_api(
            user2_token,
            title="User2's Sample Story",
            content="Once upon a time, user2 wrote a short story for a test.",
            author="user2-pseudonym"
        )
        create_text_api(
            user2_token,
            title="User2's Second Text",
            content="This is the sequel to the first text written by user2.",
            author="user2-pseudonym" # Assuming author is username, adjust if schema differs
        )

    # Step e) user1 and user2 create each an AI judge and an AI writer
    print("\n=== Step E: Users Create AI Agents ===")
    if user1_token:
        create_agent_api(
            user1_token,
            name="User1's Judge Bot",
            description="AI Judge created by user1.",
            agent_type="judge",
            prompt="You are a fair and balanced literary judge."
        )
        create_agent_api(
            user1_token,
            name="User1's Story Bot",
            description="AI Writer created by user1.",
            agent_type="writer",
            prompt="You are a creative storyteller."
        )
    if user2_token:
        create_agent_api(
            user2_token,
            name="User2's Critical Eye",
            description="AI Judge created by user2.",
            agent_type="judge",
            prompt="You are a discerning critic focusing on plot and character."
        )
        create_agent_api(
            user2_token,
            name="User2's Poem Generator",
            description="AI Writer created by user2.",
            agent_type="writer",
            prompt="You are a poet specializing in haikus."
        )

    # Step f) repeat the same but with the admin
    if admin_token:
        print("\n=== Step F: Admin Actions ===")
        # Admin creates a private contest
        create_contest_api(
            admin_token,
            title="Admin's Private Test Contest",
            description="This is a private contest created by admin. Password is 'adminpass'.",
            is_private=True,
            password="adminpass"
        )
        # Admin creates a public contest
        create_contest_api(
            admin_token,
            title="Admin's Public Showcase",
            description="This is a public contest created by admin.",
            is_private=False
        )
        # Admin creates a text
        create_text_api(
            admin_token,
            title="Admin's Official Document",
            content="This document was prepared by the site administrator.",
            author="Admin" # Or admin's username
        )
        # Admin creates an AI judge (can be public)
        create_agent_api(
            admin_token,
            name="Global Judge OmniCrit",
            description="A public AI Judge provided by admin.",
            agent_type="judge",
            prompt="You are an omniscient judge evaluating all aspects of writing.",
            is_public=True
        )
        # Admin creates an AI writer (can be public)
        create_agent_api(
            admin_token,
            name="Global Writer ScribeMax",
            description="A public AI Writer provided by admin.",
            agent_type="writer",
            prompt="You can write in any style, any genre.",
            is_public=True
        )
        assign_user_credits(admin_token, 2, 10)
    else:
        print("\nSkipping Admin actions as admin token was not obtained.")

    print("\n--- Debug Init Script Finished ---") 