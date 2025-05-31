import requests
import json
import time
import os
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"

def print_response(response: requests.Response, action: str, quiet: bool = False):
    """Helper function to print API call results."""
    if not quiet:
        print(f"--- {action} ---")
    try:
        response_json = response.json()
        if not quiet:
            print(f"Status Code: {response.status_code}")
            if response.status_code < 400:
                print(f"Success: {action}")
            else:
                print(f"ERROR: {action} failed - {response_json}")
        return response_json
    except json.JSONDecodeError:
        if not quiet:
            print(f"Response (not JSON): {response.text}")
            if response.status_code >= 400:
                print(f"ERROR: {action} failed.")
        return None

# --- Authentication ---
def signup_user(username, email, password, quiet=True):
    payload = {"username": username, "email": email, "password": password}
    response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    return print_response(response, f"Signup User: {username}", quiet)

def login_user(username, password, quiet=True):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", data=payload)
    data = print_response(response, f"Login User: {username}", quiet)
    if data and "access_token" in data:
        return data["access_token"]
    return None

def get_user_info_api(token, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    return print_response(response, "Get Current User Info", quiet)

# --- Resource Creation ---
def create_contest_api(token, title, description, password_protected=False, publicly_listed=True, password=None, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "description": description,
        "password_protected": password_protected,
        "publicly_listed": publicly_listed,
        "min_votes_required": 1,
    }
    if password_protected and password:
        payload["password"] = password
    
    response = requests.post(f"{BASE_URL}/contests/", headers=headers, json=payload)
    return print_response(response, f"Create Contest: {title}", quiet)

def create_text_api(token, title, content, author, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title, "content": content, "author": author}
    response = requests.post(f"{BASE_URL}/texts/", headers=headers, json=payload)
    return print_response(response, f"Create Text: {title}", quiet)

def create_agent_api(token, name, description, agent_type, prompt, model="default_model_for_testing", is_public=False, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "description": description,
        "type": agent_type,
        "prompt": prompt,
        "model": model, 
        "is_public": is_public
    }
    response = requests.post(f"{BASE_URL}/agents/", headers=headers, json=payload)
    return print_response(response, f"Create Agent: {name} ({agent_type})", quiet)

def submit_text_to_contest_api(token, contest_id, text_id, password=None, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"text_id": text_id}
    params = {}
    if password:
        params["password"] = password
    
    response = requests.post(f"{BASE_URL}/contests/{contest_id}/submissions/", 
                           headers=headers, json=payload, params=params)
    return print_response(response, f"Submit Text {text_id} to Contest {contest_id}", quiet)

def assign_ai_judge_to_contest_api(token, contest_id, agent_id, quiet=True):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"agent_judge_id": agent_id}
    
    response = requests.post(f"{BASE_URL}/contests/{contest_id}/judges", 
                           headers=headers, json=payload)
    return print_response(response, f"Assign AI Judge (Agent {agent_id}) to Contest {contest_id}", quiet)

# --- Admin Functions ---
def get_admin_credentials():
    """Get admin credentials from environment variables"""
    username = os.getenv('ADMIN_USERNAME')
    email = os.getenv('ADMIN_EMAIL') 
    password = os.getenv('ADMIN_PASSWORD')
    
    if not all([username, email, password]):
        print("❌ Missing admin credentials in environment variables")
        print("Please set ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD in .env file")
        return None, None, None
    
    return username, email, password

def login_admin():
    """Login admin user and return token"""
    username, email, password = get_admin_credentials()
    if not username:
        return None
    
    # Login admin
    token = login_user(username, password, quiet=True)
    if token:
        print("✅ Admin user logged in successfully")
        return token
    else:
        print("❌ Failed to login admin user")
        return None

def assign_credits_to_user_api(admin_token, user_id, credits, description, quiet=True):
    """Admin function to assign credits to a user"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "credits": credits,  # Fixed: use 'credits' instead of 'amount'
        "description": description
    }
    
    response = requests.patch(f"{BASE_URL}/admin/users/{user_id}/credits", 
                            headers=headers, json=payload)
    return print_response(response, f"Assign {credits} credits to User {user_id}", quiet)

# --- User Data Structures ---
class UserData:
    def __init__(self, username: str, token: str, user_id: int):
        self.username = username
        self.token = token
        self.user_id = user_id
        self.texts: List[int] = []
        self.contests: List[int] = []
        self.writers: List[int] = []
        self.judges: List[int] = []

def create_regular_user(user_num: int) -> Optional[UserData]:
    """Create a regular user with 1 text, 1 contest, 1 writer, 1 judge"""
    username = f"user{user_num:03d}"
    email = f"{username}@test.plumas.top"
    password = "123123"
    
    # Sign up user
    signup_response = signup_user(username, email, password)
    if not signup_response:
        print(f"Failed to create user {username}")
        return None
    
    # Login user
    token = login_user(username, password)
    if not token:
        print(f"Failed to login user {username}")
        return None
    
    # Get user info
    user_info = get_user_info_api(token)
    if not user_info or "id" not in user_info:
        print(f"Failed to get user info for {username}")
        return None
    
    user_data = UserData(username, token, user_info["id"])
    
    # Create 1 text
    text_response = create_text_api(
        token,
        f"{username}'s Sample Text",
        f"This is a sample text written by {username}. " * 20,
        f"{username}-author"
    )
    if text_response and "id" in text_response:
        user_data.texts.append(text_response["id"])
    
    # Create 1 public contest
    contest_response = create_contest_api(
        token,
        f"{username}'s Public Contest",
        f"A public writing contest created by {username}.",
        publicly_listed=True
    )
    if contest_response and "id" in contest_response:
        user_data.contests.append(contest_response["id"])
    
    # Create 1 AI writer
    writer_response = create_agent_api(
        token,
        f"{username} Writer Bot",
        f"AI Writer created by {username}",
        "writer",
        f"You are a creative writer working for {username}. Write engaging stories."
    )
    if writer_response and "id" in writer_response:
        user_data.writers.append(writer_response["id"])
    
    # Create 1 AI judge
    judge_response = create_agent_api(
        token,
        f"{username} Judge Bot",
        f"AI Judge created by {username}",
        "judge",
        f"You are a fair literary judge working for {username}. Evaluate texts objectively."
    )
    if judge_response and "id" in judge_response:
        user_data.judges.append(judge_response["id"])
    
    return user_data

def create_special_user(user_num: int) -> Optional[UserData]:
    """Create a special user with 30 texts, multiple contests, 30 writers, 30 judges"""
    username = f"special{user_num:02d}"
    email = f"{username}@test.plumas.top"
    password = "123123"
    
    # Sign up user
    signup_response = signup_user(username, email, password)
    if not signup_response:
        print(f"Failed to create special user {username}")
        return None
    
    # Login user
    token = login_user(username, password)
    if not token:
        print(f"Failed to login special user {username}")
        return None
    
    # Get user info
    user_info = get_user_info_api(token)
    if not user_info or "id" not in user_info:
        print(f"Failed to get user info for special user {username}")
        return None
    
    user_data = UserData(username, token, user_info["id"])
    
    print(f"Creating content for special user {username}...")
    
    # Create 30 texts
    for i in range(30):
        text_response = create_text_api(
            token,
            f"{username}'s Text #{i+1}",
            f"This is text number {i+1} written by special user {username}. " * 30,
            f"{username}-author"
        )
        if text_response and "id" in text_response:
            user_data.texts.append(text_response["id"])
    
    # Create multiple contests
    for i in range(5):  # 5 contests per special user
        contest_response = create_contest_api(
            token,
            f"{username}'s Elite Contest #{i+1}",
            f"An elite writing contest #{i+1} created by special user {username}.",
            publicly_listed=True
        )
        if contest_response and "id" in contest_response:
            user_data.contests.append(contest_response["id"])
    
    # Create 30 AI writers
    for i in range(30):
        writer_response = create_agent_api(
            token,
            f"{username} Writer Bot #{i+1}",
            f"AI Writer #{i+1} created by special user {username}",
            "writer",
            f"You are creative writer #{i+1} working for {username}. Specialize in genre #{i % 10}."
        )
        if writer_response and "id" in writer_response:
            user_data.writers.append(writer_response["id"])
    
    # Create 30 AI judges
    for i in range(30):
        judge_response = create_agent_api(
            token,
            f"{username} Judge Bot #{i+1}",
            f"AI Judge #{i+1} created by special user {username}",
            "judge",
            f"You are literary judge #{i+1} working for {username}. Focus on aspect #{i % 10}."
        )
        if judge_response and "id" in judge_response:
            user_data.judges.append(judge_response["id"])
    
    return user_data

def main():
    print("Starting Large Scale Duelo de Plumas Data Generation...")
    print("This script will create 300 regular users + 10 special users with their content.")
    print("This may take a significant amount of time. Please be patient.\n")
    
    all_users: List[UserData] = []
    special_users: List[UserData] = []
    
    # Create 300 regular users
    print("=== Creating 300 Regular Users ===")
    for i in range(1, 301):
        if i % 50 == 0:
            print(f"Progress: {i}/300 regular users created...")
        
        user_data = create_regular_user(i)
        if user_data:
            all_users.append(user_data)
        
        # Small delay to avoid overwhelming the server
        #time.sleep(0.1)
    
    print(f"✅ Created {len(all_users)} regular users successfully")
    
    # Create 10 special users
    print("\n=== Creating 10 Special Users ===")
    for i in range(1, 11):
        print(f"Creating special user {i}/10...")
        
        user_data = create_special_user(i)
        if user_data:
            special_users.append(user_data)
            all_users.append(user_data)
        
        # Longer delay for special users due to more content
        #time.sleep(0.5)
    
    print(f"✅ Created {len(special_users)} special users successfully")
    
    # Create Contest 1: All users submit one text
    print("\n=== Creating Contest 1: Mass Participation ===")
    if special_users:
        creator = special_users[0]
        contest1_response = create_contest_api(
            creator.token,
            "Mass Participation Contest",
            "A large contest where all users submit one text. Created for testing scale.",
            publicly_listed=True,
            quiet=False
        )
        
        if contest1_response and "id" in contest1_response:
            contest1_id = contest1_response["id"]
            print(f"Contest 1 created with ID: {contest1_id}")
            
            # All users submit their first text
            submitted_count = 0
            for user in all_users:
                if user.texts:
                    submit_response = submit_text_to_contest_api(
                        user.token, contest1_id, user.texts[0]
                    )
                    if submit_response:
                        submitted_count += 1
            
            print(f"✅ {submitted_count} users submitted texts to Contest 1")
    
    # Create Contest 2: Special users only + AI judges
    print("\n=== Creating Contest 2: Elite Contest with AI Judges ===")
    if special_users:
        creator = special_users[0]
        contest2_response = create_contest_api(
            creator.token,
            "Elite AI-Judged Contest",
            "An exclusive contest for special users, judged by 10 AI judges.",
            publicly_listed=True,
            quiet=False
        )
        
        if contest2_response and "id" in contest2_response:
            contest2_id = contest2_response["id"]
            print(f"Contest 2 created with ID: {contest2_id}")
            
            # Special users submit one text each
            submitted_count = 0
            for user in special_users:
                if user.texts:
                    submit_response = submit_text_to_contest_api(
                        user.token, contest2_id, user.texts[0]
                    )
                    if submit_response:
                        submitted_count += 1
            
            print(f"✅ {submitted_count} special users submitted texts to Contest 2")
            
            # Creator assigns 10 AI judges
            judges_assigned = 0
            if creator.judges:
                for i, judge_id in enumerate(creator.judges[:10]):
                    assign_response = assign_ai_judge_to_contest_api(
                        creator.token, contest2_id, judge_id
                    )
                    if assign_response:
                        judges_assigned += 1
            
            print(f"✅ {judges_assigned} AI judges assigned to Contest 2")
    
    # Assign 1 credit to each user
    print("\n=== Assigning Credits to All Users ===")
    admin_token = login_admin()
    if admin_token:
        credits_assigned = 0
        for user in all_users:
            assign_response = assign_credits_to_user_api(
                admin_token, 
                user.user_id, 
                1, 
                "Welcome bonus - 1 credit for new user"
            )
            if assign_response:
                credits_assigned += 1
        
        print(f"✅ Assigned 1 credit to {credits_assigned} users")
    else:
        print("❌ Could not assign credits - admin login failed")
    
    print("\n" + "="*60)
    print("🎉 LARGE SCALE DATA GENERATION COMPLETE! 🎉")
    print("="*60)
    print(f"📊 Summary:")
    print(f"   • Total users created: {len(all_users)}")
    print(f"   • Regular users: {len(all_users) - len(special_users)}")
    print(f"   • Special users: {len(special_users)}")
    print(f"   • Total texts: {sum(len(user.texts) for user in all_users)}")
    print(f"   • Total contests: {sum(len(user.contests) for user in all_users)}")
    print(f"   • Total AI writers: {sum(len(user.writers) for user in all_users)}")
    print(f"   • Total AI judges: {sum(len(user.judges) for user in all_users)}")
    print(f"   • Special contests created: 2")
    print("="*60)

if __name__ == "__main__":
    main() 