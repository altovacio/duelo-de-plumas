import os
import sys

# Ensure the main project directory is in the Python path
# Adjust the path depth ('..') if init_db.py is nested deeper
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# --- Import your initialization scripts --- 
# Adjust these imports based on the actual structure and function names
# in your scripts. These are placeholders.
try:
    # Example: Assuming create_admin.py has a main function like run()
    # from create_admin import run as run_create_admin
    pass # Replace pass with your actual import
except ImportError:
    print("Warning: Could not import 'create_admin'. Skipping admin creation.")
    def run_create_admin(): print("Skipping admin creation...") # Placeholder

try:
    # Example: Assuming seed_ai_judges.py has a main function like run()
    # from seed_ai_judges import run as run_seed_ai_judges
    pass # Replace pass with your actual import
except ImportError:
    print("Warning: Could not import 'seed_ai_judges'. Skipping AI judges seeding.")
    def run_seed_ai_judges(): print("Skipping AI judges seeding...") # Placeholder

try:
    from seed_contest import run_seeding as run_seed_contest
except ImportError:
    print("Error: Could not import 'seed_contest'. Cannot seed contest data.")
    # Exit if this crucial step fails
    sys.exit(1) 

def initialize_database():
    """Runs all the necessary steps to initialize the database."""
    print("--- Starting Database Initialization ---")

    print("\nStep 1: Creating Admin User...")
    try:
        # run_create_admin() # Uncomment and adjust once imported
        print("Admin user creation step placeholder.") # Placeholder
    except Exception as e:
        print(f"Error during admin creation: {e}")

    print("\nStep 2: Seeding AI Judges...")
    try:
        # run_seed_ai_judges() # Uncomment and adjust once imported
        print("AI judges seeding step placeholder.") # Placeholder
    except Exception as e:
        print(f"Error during AI judges seeding: {e}")

    print("\nStep 3: Seeding Contest Data...")
    try:
        run_seed_contest()
    except Exception as e:
        print(f"Error during contest seeding: {e}")

    print("\n--- Database Initialization Complete ---")

if __name__ == "__main__":
    initialize_database() 