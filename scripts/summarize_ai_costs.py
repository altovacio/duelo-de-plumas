import httpx
import asyncio
import os
import sys
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
# --- End Configuration ---

async def login_admin(client: httpx.AsyncClient):
    """Logs in the admin user and returns the token."""
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        print("Error: ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set.")
        return None
        
    login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    try:
        response = await client.post(f"{BASE_URL}/auth/token", data=login_data)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        token = response.json().get("access_token")
        if not token:
            print("Error: Admin login successful but no token found.")
            return None
        print(f"Admin login successful for user: {ADMIN_USERNAME}")
        return token
    except httpx.RequestError as exc:
        print(f"Error during admin login request: {exc}")
        return None
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while logging in admin: {exc.response.text}")
        return None

async def get_all_user_ids(client: httpx.AsyncClient, token: str):
    """Fetches all user IDs using the admin endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    # Fetch users with a large limit to try and get all
    users_url = f"{BASE_URL}/admin/users/?limit=10000" 
    try:
        response = await client.get(users_url, headers=headers)
        response.raise_for_status()
        users = response.json()
        # Extract IDs and print usernames for debugging
        user_ids = []
        print("DEBUG: Fetched users:")
        for user in users:
            user_id = user.get('id')
            username = user.get('username')
            print(f"  - ID: {user_id}, Username: {username}") # DEBUG
            if user_id is not None:
                user_ids.append(user_id)
        print(f"Found {len(user_ids)} user IDs.")
        return user_ids
    except httpx.RequestError as exc:
        print(f"Error during get users request: {exc}")
        return []
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while getting users: {exc.response.text}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while getting user IDs: {e}")
        return []

async def get_credit_history(client: httpx.AsyncClient, user_id: int, token: str):
    """Fetches the credit history for a given user ID."""
    headers = {"Authorization": f"Bearer {token}"}
    # Fetch history - limit large enough? CostLedger might grow.
    history_url = f"{BASE_URL}/admin/users/{user_id}/credit-history?limit=10000" 
    try:
        response = await client.get(history_url, headers=headers)
        # Don't raise for 404, as history should be retrievable even for deleted users
        if response.status_code == 404:
            print(f"Note: User {user_id} not found, but attempting to retrieve history anyway.")
            # If the endpoint returns 404 even when it shouldn't, we might get empty list here
            # If it correctly returns 200 with history, this check isn't needed.
            pass # Proceed to try and parse JSON
        elif response.status_code != 200:
             response.raise_for_status() # Raise for other errors
             
        return response.json()
    except httpx.RequestError as exc:
        print(f"Error during credit history request for user {user_id}: {exc}")
        return None
    except httpx.HTTPStatusError as exc:
        # Log 404 specifically if needed, otherwise handled above
        if exc.response.status_code != 404:
             print(f"Error response {exc.response.status_code} while fetching history for user {user_id}: {exc.response.text}")
        else:
             # Potentially return empty list if 404 means no history (depends on API fix)
             print(f"Got 404 fetching history for user {user_id}. Assuming no history or user truly gone.")
             return [] 
        return None
    except Exception as e:
        print(f"An unexpected error occurred fetching history for user {user_id}: {e}")
        return None

async def main():
    """Main function to login, fetch all users, get history for each, and aggregate costs."""
    grand_total_credits_spent = 0
    grand_total_real_cost = 0.0
    grand_total_ai_actions = 0
    processed_user_count = 0

    async with httpx.AsyncClient() as client:
        admin_token = await login_admin(client)
        if not admin_token:
            return # Stop if admin login fails

        # Removed: Fetching list of all user IDs
        # print("\nFetching list of all user IDs...")
        # user_ids = await get_all_user_ids(client, admin_token)
        # print(f"DEBUG: Fetched User IDs: {user_ids}") # DEBUG
        # if not user_ids:
        #     print("No user IDs found or failed to retrieve users. Cannot summarize costs.")
        #     return
            
        # --- Brute-force check for IDs 1 to 100 ---
        user_ids_to_check = range(1, 101) 
        print(f"\nIterating through User IDs {user_ids_to_check.start} to {user_ids_to_check.stop - 1} to fetch history and aggregate costs...")

        for user_id in user_ids_to_check:
            # Minimal print to avoid spamming, uncomment if needed
            # print(f"-- Processing User ID: {user_id} --") 
            ledger_entries = await get_credit_history(client, user_id, admin_token)

            if ledger_entries is None:
                print(f"   DEBUG: get_credit_history returned None for user {user_id}") # DEBUG
                print(f"   -> Failed to retrieve credit history for user {user_id}. Skipping.")
                continue 
            
            print(f"   DEBUG: Retrieved {len(ledger_entries)} entries for user {user_id}") # DEBUG

            processed_user_count += 1
            user_credits_spent = 0
            user_real_cost = 0.0
            user_ai_actions = 0

            if not isinstance(ledger_entries, list):
                print(f"   -> WARN: Expected list for ledger entries for user {user_id}, got {type(ledger_entries)}. Skipping.")
                continue

            # print(f"   -> Processing {len(ledger_entries)} entries for user {user_id}...") # Verbose
            for entry in ledger_entries:
                action = entry.get("action_type")
                credits_change = entry.get("credits_change") # Get value or None
                real_cost = entry.get("real_cost") # Get value or None
               
                # DEBUG: Print details of each entry being processed
                print(f"    DEBUG Entry: ID={entry.get('id')}, Action='{action}', Change={credits_change}, Cost={real_cost}")

                if action in ['ai_generate', 'ai_evaluate']:
                    user_ai_actions += 1
                    # Ensure values are not None before processing
                    current_credits_change = credits_change if credits_change is not None else 0
                    current_real_cost = float(real_cost) if real_cost is not None else 0.0

                    user_credits_spent += abs(current_credits_change)
                    user_real_cost += current_real_cost
            
            # Optional: Print per-user summary
            # print(f"   -> User {user_id} Summary: Actions={user_ai_actions}, Credits={user_credits_spent}, Cost=${user_real_cost:.6f}")
            
            # Add to grand totals
            grand_total_ai_actions += user_ai_actions
            grand_total_credits_spent += user_credits_spent
            grand_total_real_cost += user_real_cost

        print("\n--- Overall Cost Summary (Checked IDs 1-100) ---")
        print(f"Histories found for {processed_user_count} out of {len(user_ids_to_check)} IDs checked.")
        print(f"Total AI Actions recorded across checked users: {grand_total_ai_actions}")
        print(f"Total Credits Spent on AI actions across checked users: {grand_total_credits_spent}")
        print(f"Total Real Cost ($) for AI actions across checked users: ${grand_total_real_cost:.6f}")

if __name__ == "__main__":
    # Removed command-line argument handling
    # if len(sys.argv) != 2:
    #     print("Usage: python scripts/summarize_ai_costs.py <user_id>")
    #     sys.exit(1)
    # 
    # try:
    #     target_user_id = int(sys.argv[1])
    # except ValueError:
    #     print("Error: User ID must be an integer.")
    #     sys.exit(1)

    print("Running script to summarize AI costs for ALL users...")
    asyncio.run(main())