from app import create_app, db
from app.models import AIWritingRequest
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Update AI writing requests with missing version information')
    parser.add_argument('--version', default="0.2.0", help='Version to set for requests without version (default: 0.2.0)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    parser.add_argument('--all', action='store_true', help='Update all requests, not just those with NULL version')
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        # Find writing requests with NULL version
        if args.all:
            requests_to_update = db.session.scalars(db.select(AIWritingRequest)).all()
        else:
            requests_to_update = db.session.scalars(
                db.select(AIWritingRequest).where(AIWritingRequest.app_version == None)
            ).all()
        
        print(f"Found {len(requests_to_update)} AI writing requests to update")
        
        if args.dry_run:
            print("\nDRY RUN - No changes will be made")
        else:
            print("\nUpdating records...")
        
        for request in requests_to_update:
            old_version = request.app_version
            if args.dry_run:
                print(f"Would update request ID {request.id}: {old_version} → {args.version}")
            else:
                request.app_version = args.version
                print(f"Updated request ID {request.id}: {old_version} → {args.version}")
        
        if not args.dry_run and requests_to_update:
            db.session.commit()
            print(f"\nSuccessfully updated {len(requests_to_update)} records")
        
        print("\nDone!")

if __name__ == "__main__":
    main() 