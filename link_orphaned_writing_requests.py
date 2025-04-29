from app import create_app, db
from app.models import AIWritingRequest, Submission
import argparse

def find_orphaned_requests():
    """Find writing requests without linked submissions"""
    return db.session.scalars(
        db.select(AIWritingRequest).where(AIWritingRequest.submission_id == None)
    ).all()

def find_ai_submissions():
    """Find all AI-generated submissions"""
    return db.session.scalars(
        db.select(Submission).where(Submission.is_ai_generated == True)
    ).all()

def match_requests_to_submissions(orphaned_requests, ai_submissions):
    """Match writing requests to submissions based on contest_id and ai_writer_id"""
    matches = []
    unmatched_submissions = []
    
    # Create a copy of the list to work with
    available_requests = orphaned_requests.copy()
    
    for submission in ai_submissions:
        # Try to find a matching orphaned request
        matching_requests = [r for r in available_requests 
                            if r.contest_id == submission.contest_id
                            and r.ai_writer_id == submission.ai_writer_id]
        
        if matching_requests:
            # Use the first matching request
            matched_request = matching_requests[0]
            matches.append((submission, matched_request))
            # Remove this request so it's not matched again
            available_requests.remove(matched_request)
        else:
            unmatched_submissions.append(submission)
    
    # Return remaining unmatched requests
    remaining_requests = available_requests
    
    return matches, unmatched_submissions, remaining_requests

def update_database(matches, dry_run=False):
    """Update the database with the matches"""
    if dry_run:
        print("\nDRY RUN - No changes will be made")
        for sub, req in matches:
            print(f"Would link submission ID {sub.id} ({sub.title}) to writing request ID {req.id}")
        return
    
    print("\nUpdating records...")
    for sub, req in matches:
        req.submission_id = sub.id
        print(f"Linked submission ID {sub.id} ({sub.title}) to writing request ID {req.id}")
    
    db.session.commit()
    print(f"\nSuccessfully linked {len(matches)} submissions to writing requests")

def print_unmatched_items(unmatched_submissions, unmatched_requests):
    """Print details of unmatched items"""
    print("\nUnmatched submissions:")
    for sub in unmatched_submissions:
        print(f"Submission ID {sub.id}: {sub.title}")
    
    print("\nUnmatched writing requests:")
    for req in unmatched_requests:
        print(f"Writing request ID {req.id} for contest {req.contest_id}, AI writer {req.ai_writer_id}")

def main():
    parser = argparse.ArgumentParser(description='Link orphaned AI writing requests with AI-generated submissions')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        # Find orphaned requests and AI submissions
        orphaned_requests = find_orphaned_requests()
        print(f"Found {len(orphaned_requests)} orphaned AI writing requests")
        
        ai_submissions = find_ai_submissions()
        print(f"Found {len(ai_submissions)} AI-generated submissions")
        
        # Match requests to submissions
        matches, unmatched_submissions, unmatched_requests = match_requests_to_submissions(
            orphaned_requests, ai_submissions
        )
        
        print(f"Found {len(matches)} potential matches")
        print(f"{len(unmatched_submissions)} submissions remain unmatched")
        print(f"{len(unmatched_requests)} writing requests remain unmatched")
        
        # Update database if not in dry run mode
        update_database(matches, args.dry_run)
        
        # Print unmatched items
        print_unmatched_items(unmatched_submissions, unmatched_requests)
        
        print("\nDone!")

if __name__ == "__main__":
    main() 