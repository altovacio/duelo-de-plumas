#!/usr/bin/env python
from app import create_app, db
from app.models import User, Contest, Submission, Vote, UserRole # Import UserRole
from datetime import datetime
# TEMP: Comment out import as function is currently commented out in routes.py
# from app.contest.routes import calculate_contest_results # Import the function
import os
import click # Import click for CLI commands

app = create_app()

# Flask shell context processor
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Contest': Contest, 'Submission': Submission, 'Vote': Vote}

# CLI Command to check contest statuses and trigger results calculation
@app.cli.command("check-contests")
def check_contests_command():
    """Check contest statuses: open->evaluation, evaluation->closed (if ready)."""
    print("WARNING: calculate_contest_results is currently disabled for debugging.") # Add warning
    now = datetime.utcnow()
    print(f"Checking contest statuses at {now} UTC...")
    
    # --- Check Open -> Evaluation --- 
    expired_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'open')
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
            # results_calculated = calculate_contest_results(contest.id) # TEMP: Cannot call commented function
            results_calculated = False # TEMP: Assume false
            if results_calculated:
                # ... (code unreachable for now) ...
                pass
            else:
                print(f"Contest ID {contest.id}: Results calculation currently disabled or failed.") # Adjusted message
        if count_to_closed > 0:
            print(f"Calculated results and closed {count_to_closed} contest(s).")
        else:
            print("No contests in evaluation were ready for results calculation.")
    else:
        print("No contests currently in evaluation phase.")

# --- New CLI Command to Create Admin User --- 
@app.cli.command("create-admin")
@click.option('--username', prompt=True, default='admin', help='Username for the admin account.')
@click.option('--email', prompt=True, help='Email address for the admin account.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the admin account.')
def create_admin_command(username, email, password):
    """Creates the initial admin user."""
    if db.session.scalar(db.select(User).where(User.username == username)):
        click.echo(f'Error: Username "{username}" already exists.')
        return
    if db.session.scalar(db.select(User).where(User.email == email)):
        click.echo(f'Error: Email "{email}" already exists.')
        return
    
    admin_user = User(
        username=username,
        email=email,
        role=UserRole.ADMIN, # Use the Enum member
        judge_type=None # Admins don't need a judge type
    )
    admin_user.set_password(password)
    db.session.add(admin_user)
    try:
        db.session.commit()
        click.echo(f'Admin user "{username}" created successfully.')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {e}')

if __name__ == '__main__':
    # Use debug=True for development, turn off for production
    app.run(debug=True) 