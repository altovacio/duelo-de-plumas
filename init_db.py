import os
import sys
import time # Import time for delay

# Ensure the main project directory is in the Python path
# Adjust the path depth ('..') if init_db.py is nested deeper
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import app and db AFTER setting path
from app import create_app, db

# --- Import your data seeding/initialization scripts --- 
# Adjust these imports based on the actual structure and function names
# in your scripts. These are placeholders.
try:
    # Example: Assuming create_admin.py has a main function like run()
    from create_admin import create_admin_user
    # pass # Replace pass with your actual import
except ImportError:
    print("Warning: Could not import 'create_admin'. Skipping admin creation.")
    def create_admin_user(): print("Skipping admin creation...") # Placeholder

try:
    # Example: Assuming seed_ai_judges.py has a main function like run()
    from seed_ai_judges import create_ai_judges
    # pass # Replace pass with your actual import
except ImportError:
    print("Warning: Could not import 'seed_ai_judges'. Skipping AI judges seeding.")
    def create_ai_judges(): print("Skipping AI judges seeding...") # Placeholder

try:
    # Import seed_ai_writers.py function
    from seed_ai_writers import create_ai_writers
except ImportError:
    print("Warning: Could not import 'seed_ai_writers'. Skipping AI writers seeding.")
    def create_ai_writers(): print("Skipping AI writers seeding...") # Placeholder

try:
    from seed_contest import run_seeding as run_seed_contest
except ImportError:
    print("Error: Could not import 'seed_contest'. Cannot seed contest data.")
    # Exit if this crucial step fails
    sys.exit(1) 

def initialize_database(app):
    """Drops existing tables, creates new ones, and seeds initial data."""
    with app.app_context():
        print("--- Starting Database Initialization ---")
        
        # Determine DB path from config (assuming SQLite)
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            print(f"Deleting existing database: {db_path}")
            try:
                os.remove(db_path)
                print("Existing database deleted.")
                # Add a small delay to ensure file system releases the lock
                time.sleep(0.5) 
            except OSError as e:
                print(f"Error deleting database file: {e}")
                print("Please ensure no other process is using the database file.")
                sys.exit(1)
        else:
            print("No existing database found.")
        
        print("\nStep 1: Creating database tables...")
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            sys.exit(1)

        print("\nStep 2: Creating Admin User...")
        try:
            create_admin_user()
        except Exception as e:
            print(f"Error during admin creation: {e}")

        print("\nStep 3: Seeding AI Judges...")
        try:
            create_ai_judges()
        except Exception as e:
            print(f"Error during AI judges seeding: {e}")

        print("\nStep 4: Seeding AI Writers...")
        try:
            create_ai_writers()
        except Exception as e:
            print(f"Error during AI writers seeding: {e}")

        print("\nStep 5: Seeding Contest Data...")
        try:
            run_seed_contest()
        except Exception as e:
            print(f"Error during contest seeding: {e}")

        print("\n--- Database Initialization Complete ---")

if __name__ == "__main__":
    # Create a Flask app instance to provide context
    app_instance = create_app()
    initialize_database(app_instance) 