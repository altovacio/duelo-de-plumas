from flask import render_template, url_for, redirect, request
from flask_login import current_user
from app.main import bp
from app.models import Contest, User, Submission, Vote # Import Vote
from app import db
from datetime import datetime

@bp.route('/')
@bp.route('/index')
def index():
    current_time = datetime.utcnow()
    # Fetch active public contests
    active_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.contest_type == 'public')
        .where(Contest.status == 'open')
        .where(Contest.end_date > current_time)
        .order_by(Contest.end_date.asc())
    ).all()

    # Fetch recently closed contests (all for now, limit later if needed)
    closed_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'closed')
        .order_by(Contest.end_date.desc())
    ).all()

    # Fetch pending evaluations for the current judge
    judge_assigned_evaluations = []
    if current_user.is_authenticated and current_user.role == 'judge':
        judge_assigned_evaluations = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .where(Contest.judges.any(User.id == current_user.id))
            .order_by(Contest.end_date.asc())
        ).all()
    
    # Fetch contests requiring AI evaluations (for admins)
    pending_ai_evaluations = []
    if current_user.is_authenticated and current_user.is_admin():
        # Get contests in evaluation phase with assigned AI judges
        evaluation_contests = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .order_by(Contest.end_date.asc())
        ).all()
        
        for contest in evaluation_contests:
            # Get AI judges assigned to the contest
            ai_judges = db.session.scalars(
                db.select(User)
                .where(User.role == 'judge', User.judge_type == 'ai')
                .join(User.judged_contests)
                .where(Contest.id == contest.id)
            ).all()
            
            if ai_judges:
                # Get judges that have already voted
                judges_with_votes = set(db.session.scalars(
                    db.select(Vote.judge_id).distinct()
                    .join(Vote.submission)
                    .where(Submission.contest_id == contest.id)
                ).all())
                
                # Check if any AI judge hasn't voted yet
                for ai_judge in ai_judges:
                    if ai_judge.id not in judges_with_votes:
                        # Found an AI judge that hasn't evaluated yet
                        if contest not in pending_ai_evaluations:
                            pending_ai_evaluations.append(contest)
                            break

    return render_template('main/index.html', 
                           title='Inicio', 
                           active_contests=active_contests,
                           closed_contests=closed_contests,
                           judge_assigned_evaluations=judge_assigned_evaluations,
                           pending_ai_evaluations=pending_ai_evaluations,
                           Submission=Submission) # Pass Submission model

# New Route for listing all contests by status
@bp.route('/contests')
def list_contests():
    now = datetime.utcnow()
    # Public lists
    contests_open = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'open')
        .where(Contest.end_date > now)
        .order_by(Contest.end_date.asc())
    ).all()
    
    contests_evaluation = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'evaluation')
        .order_by(Contest.end_date.desc())
    ).all()
    
    contests_closed = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'closed')
        .order_by(Contest.end_date.desc())
    ).all()
    
    # Judge specific list
    judge_assigned_evaluations = []
    if current_user.is_authenticated and current_user.role == 'judge':
        judge_assigned_evaluations = db.session.scalars(
            # Select contests where status is evaluation AND current user is in the judges list
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .where(Contest.judges.any(User.id == current_user.id)) # Check relationship
            .order_by(Contest.end_date.asc())
        ).all()
    
    return render_template('main/contests.html', 
                           title='Concursos Literarios', 
                           contests_open=contests_open,
                           contests_evaluation=contests_evaluation,
                           contests_closed=contests_closed,
                           judge_assigned_evaluations=judge_assigned_evaluations,
                           Submission=Submission) # Pass Submission model

# Add other main routes here (e.g., about page) 