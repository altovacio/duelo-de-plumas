#!/usr/bin/env python
from app import create_app, db
from app.models import User, Contest, Submission, Vote # Import models
from datetime import datetime
from app.contest.routes import calculate_contest_results # Import the function

app = create_app()

# Flask shell context processor
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Contest': Contest, 'Submission': Submission, 'Vote': Vote}

# CLI Command to check contest statuses and trigger results calculation
@app.cli.command("check-contests")
def check_contests_command():
    """Check contest statuses: open->evaluation, evaluation->closed (if ready)."""
    now = datetime.utcnow()
    print(f"Checking contest statuses at {now} UTC...")
    
    # --- Check Open -> Evaluation --- 
    expired_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'open')
        .where(Contest.end_date.is_not(None))
        .where(Contest.end_date <= now)
    ).all()
    
    count_to_eval = 0
    if expired_contests:
        for contest in expired_contests:
            print(f"Updating status for contest ID {contest.id} ('{contest.title}') from open to evaluation.")
            contest.status = 'evaluation'
            count_to_eval += 1
        db.session.commit()
        print(f"Moved {count_to_eval} contest(s) to evaluation.")
    else:
        print("No open contests found past their end date.")

    # --- Check Evaluation -> Closed (Attempt results calculation) --- 
    eval_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'evaluation')
    ).all()
    
    count_to_closed = 0
    if eval_contests:
        print(f"Checking {len(eval_contests)} contest(s) in evaluation phase...")
        for contest in eval_contests:
            print(f"Attempting result calculation for contest ID {contest.id} ('{contest.title}')...")
            results_calculated = calculate_contest_results(contest.id) # Call the function
            if results_calculated:
                count_to_closed += 1
                # The function already prints success and commits
            else:
                print(f"Contest ID {contest.id}: Not all judges have voted or calculation failed.")
        if count_to_closed > 0:
            print(f"Calculated results and closed {count_to_closed} contest(s).")
        else:
            print("No contests in evaluation were ready for results calculation.")
    else:
        print("No contests currently in evaluation phase.")

if __name__ == '__main__':
    # Use run(debug=True) for development, turn off for production
    app.run(host='0.0.0.0', port=5000, debug=True) 