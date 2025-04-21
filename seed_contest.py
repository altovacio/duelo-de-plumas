import os
import re
import sys
from datetime import datetime, timedelta, timezone

# Ensure the main project directory is in the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

import config
from app import create_app, db
from app.models import Contest, Submission

def extract_author(content):
    """Extracts the author from the text content."""
    # Match "Autor:" or "Autora:" followed by the name
    match = re.search(r"^(?:Autor|Autora):\s*(.*)", content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Autor Desconocido" # Default if not found

def extract_title_from_content(content):
    """Extracts the title from the text content."""
    match = re.search(r"^Título:\s*(.*)", content, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None

def seed_contest_in_db(examples_dir, contest_name, contest_desc, duration_days):
    """Reads text files and seeds a contest and its submissions in the database."""
    app = create_app()
    with app.app_context():
        # Check if contest already exists
        existing_contest = db.session.scalar(db.select(Contest).filter_by(title=contest_name))
        if existing_contest:
            print(f"Contest '{contest_name}' already exists in the database. Skipping seeding.")
            return

        # Create the new contest
        print(f"Creating contest '{contest_name}'...")
        end_date = datetime.now(timezone.utc) + timedelta(days=duration_days)
        new_contest = Contest(
            title=contest_name,
            description=contest_desc,
            end_date=end_date,
            status='open',
            contest_type='public' # Default to public for seeded contest
        )
        db.session.add(new_contest)
        db.session.flush() # Flush to get the new_contest.id before adding submissions

        print(f"Processing submissions from directory: {examples_dir}")
        submissions_added = 0
        if not os.path.isdir(examples_dir):
            print(f"Error: Directory '{examples_dir}' not found.")
            db.session.rollback() # Rollback contest creation if examples are missing
            return

        for filename in os.listdir(examples_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(examples_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    author_name = extract_author(content)
                    # Use title from content if available, otherwise from filename
                    title_from_content = extract_title_from_content(content)
                    title_from_filename = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                    title = title_from_content if title_from_content else title_from_filename

                    # Create Submission object
                    submission = Submission(
                        author_name=author_name, # Using the name directly from text
                        title=title,
                        text_content=content, # Store the full text
                        contest_id=new_contest.id
                    )
                    db.session.add(submission)
                    print(f"  - Added submission: '{title}' by {author_name}")
                    submissions_added += 1

                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    # Optionally rollback this specific submission or continue

        if submissions_added > 0:
            try:
                db.session.commit()
                print(f"\nSuccessfully created contest '{contest_name}' with {submissions_added} submissions.")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing contest and submissions to database: {e}")
        else:
            db.session.rollback() # Rollback contest if no submissions were added
            print("No submissions were added. Rolling back contest creation.")

def run_seeding():
    """Main function to run the contest seeding process into the DB."""
    print("Seeding contest '{config.CONTEST_NAME}' into the database...")
    seed_contest_in_db(
        config.EXAMPLES_DIR, 
        config.CONTEST_NAME, 
        config.CONTEST_DESCRIPTION,
        config.CONTEST_DURATION_DAYS
    )

if __name__ == "__main__":
    run_seeding() 