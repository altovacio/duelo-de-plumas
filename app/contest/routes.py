from flask import render_template, flash, redirect, url_for, abort, request
from flask_login import current_user, login_required # Added login_required
from app import db
from app.contest import bp
from app.contest.forms import SubmissionForm, ContestEvaluationForm, SubmissionRankForm # Use new form
from app.models import Contest, Submission, Vote, User # Added User
from datetime import datetime, timezone
from app.decorators import judge_required # Import judge_required
from sqlalchemy import func, distinct # Import func, distinct
from wtforms.validators import ValidationError # Need this for the except block
from sqlalchemy.orm import joinedload # Import joinedload
from app.services.ai_judge_service import run_ai_evaluation # Import AI judge service

@bp.route('/<int:contest_id>', methods=['GET', 'POST'])
def detail(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404) # Contest not found

    # Check if contest is public or if user needs password for private contest (implement later)
    if contest.contest_type == 'private':
        # TODO: Add password check logic here for private contests
        flash('Los concursos privados aún no están implementados.', 'warning')
        # For now, maybe redirect or show limited info
        # return redirect(url_for('main.index'))
        pass # Allow access for now during development

    form = None
    is_open = (contest.status == 'open' and contest.end_date > datetime.utcnow())
    is_evaluation = (contest.status == 'evaluation')
    is_closed = (contest.status == 'closed')
    
    submissions_list = []
    votes_list = []
    votes_by_submission = {}

    if is_open:
        form = SubmissionForm()
        if form.validate_on_submit():
            # Check if user is allowed to submit (e.g., login required? submission limits?)
            # For now, allow any submission if the form validates
            
            submission = Submission(
                author_name=form.author_name.data,
                title=form.title.data,
                text_content=form.text_content.data,
                contest_id=contest.id
                # user_id=current_user.id if current_user.is_authenticated else None # Optional: link to user
            )
            db.session.add(submission)
            db.session.commit()
            flash('Tu texto ha sido enviado exitosamente.', 'success')
            return redirect(url_for('contest.detail', contest_id=contest.id)) # Redirect to same page

    if is_closed:
        submissions_list = db.session.scalars(
            db.select(Submission)
            .where(Submission.contest_id == contest.id)
            .order_by(Submission.final_rank.asc().nulls_last(), Submission.total_points.desc(), Submission.submission_date.asc())
        ).all()
        
        votes_list = db.session.scalars(
            db.select(Vote)
            .options(joinedload(Vote.judge))
            .join(Vote.submission)
            .where(Submission.contest_id == contest.id)
        ).all()
        
        for vote in votes_list:
            if vote.submission_id not in votes_by_submission:
                votes_by_submission[vote.submission_id] = []
            votes_by_submission[vote.submission_id].append(vote)

    return render_template('contest/detail.html', 
                           title=contest.title, 
                           contest=contest, 
                           form=form, 
                           is_open=is_open,
                           is_evaluation=is_evaluation, # Pass status flags
                           is_closed=is_closed,
                           submissions_list=submissions_list, # Pass results data
                           votes_by_submission=votes_by_submission if is_closed else {} # Pass votes dict
                          )

# Route for judges to view submissions for a contest
@bp.route('/<int:contest_id>/submissions')
@login_required
@judge_required
def list_submissions(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # Check if current user is an assigned judge for this contest (or admin)
    if not current_user.is_admin() and current_user not in contest.judges.all():
        flash('No tienes permiso para evaluar este concurso.', 'danger')
        return redirect(url_for('contest.detail', contest_id=contest.id))

    if contest.status not in ['evaluation', 'closed']:
         if not current_user.is_admin():
             flash('Las sumisiones sólo pueden ser vistas/evaluadas durante la fase de evaluación o una vez cerrado el concurso.', 'warning')
             return redirect(url_for('contest.detail', contest_id=contest.id))

    submissions = db.session.scalars(
        db.select(Submission).where(Submission.contest_id == contest.id).order_by(Submission.submission_date.asc())
    ).all()

    # Check if the current judge has already submitted rankings
    has_voted = False
    if current_user.is_authenticated:
        # A simple check: see if any vote exists for this judge and contest
        # (Assumes votes are only created when a full ranking is submitted)
        vote_exists = db.session.scalar(
            db.select(Vote).where(Vote.judge_id == current_user.id)
                       .join(Vote.submission).where(Submission.contest_id == contest.id)
                       .limit(1)
        )
        has_voted = vote_exists is not None
    
    # Get AI judges assigned to this contest
    ai_judges = db.session.scalars(
        db.select(User).where(User.role == 'judge', User.judge_type == 'ai')
        .join(User.judged_contests).where(Contest.id == contest.id)
    ).all()

    return render_template('contest/list_submissions.html', 
                           title=f'Evaluar Envíos: {contest.title}', 
                           contest=contest, 
                           submissions=submissions,
                           has_voted=has_voted,
                           ai_judges=ai_judges) # Pass AI judges to template

# New route for a judge to evaluate the entire contest (ranking)
@bp.route('/contest/<int:contest_id>/evaluate', methods=['GET', 'POST'])
@login_required
@judge_required
def evaluate_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    if not current_user.is_admin() and current_user not in contest.judges.all():
        flash('No tienes permiso para evaluar este concurso.', 'danger')
        return redirect(url_for('contest.detail', contest_id=contest.id))
    
    if contest.status != 'evaluation':
        flash('Sólo se puede evaluar durante la fase de evaluación.', 'warning')
        return redirect(url_for('contest.detail', contest_id=contest.id))

    submissions = db.session.scalars(
        db.select(Submission).where(Submission.contest_id == contest.id)
    ).all()
    submission_count = len(submissions)

    # --- Refactored Form Population --- 
    # 1. Fetch existing votes for the current judge
    existing_votes_query = db.session.scalars(
        db.select(Vote).where(Vote.judge_id == current_user.id)
                   .join(Vote.submission).where(Submission.contest_id == contest.id)
    ).all()
    existing_votes = {v.submission_id: v for v in existing_votes_query}

    # 2. Prepare data for the form constructor
    submissions_data = []
    for sub in submissions:
        sub_data = {
            'submission_id': sub.id,
            'place': 0, # Default place
            'comment': '' # Default comment
        }
        if sub.id in existing_votes:
            vote_data = existing_votes[sub.id]
            sub_data['place'] = vote_data.place or 0
            sub_data['comment'] = vote_data.comment or ''
        submissions_data.append(sub_data)
    
    # 3. Instantiate the form with the prepared data
    #    Only pass data on GET or if validation failed (implicitly handled by WTForms)
    if request.method == 'GET': 
        form = ContestEvaluationForm(data={'submissions': submissions_data})
    else: # POST request (validation likely failed if we are here)
        form = ContestEvaluationForm() # Let WTForms repopulate from request.form
    # --- End Refactored Form Population ---

    if request.method == 'POST' and form.validate_on_submit():
        # Custom validation first
        try:
            form.validate_ranking(submission_count)
        except ValidationError as e:
            flash(str(e), 'danger')
            # Fall through to re-render the template with errors
        else: # Validation passed
            # Delete existing votes for this judge and contest
            Vote.query.filter(
                Vote.judge_id == current_user.id,
                Vote.submission.has(contest_id=contest.id)
            ).delete(synchronize_session='fetch') # Added synchronize_session

            # Create new votes based on form data
            votes_to_add = []
            for submission_form in form.submissions:
                place = submission_form.place.data
                sub_id = int(submission_form.submission_id.data)
                comment_text = submission_form.comment.data # Get comment for this submission
                
                # Save vote only if place is assigned OR comment is provided
                if place != 0 or comment_text:
                    vote = Vote(
                        judge_id=current_user.id,
                        submission_id=sub_id,
                        place=place if place != 0 else None, # Store None if no place selected
                        comment=comment_text
                    )
                    votes_to_add.append(vote)

            db.session.add_all(votes_to_add)
            db.session.commit()
            flash('Ranking y comentarios guardados exitosamente.', 'success') # Updated message

            # Attempt to calculate results
            results_calculated = calculate_contest_results(contest.id)
            if results_calculated:
                flash('¡Todos los jueces requeridos han votado! Resultados calculados y concurso cerrado.', 'info')
                return redirect(url_for('contest.detail', contest_id=contest.id))
            else:
                return redirect(url_for('contest.list_submissions', contest_id=contest.id))

    return render_template('contest/evaluate_contest.html', 
                           title=f'Evaluar: {contest.title}', 
                           contest=contest,
                           submissions=submissions,
                           form=form)

# New route to run AI evaluation
@bp.route('/contest/<int:contest_id>/run_ai_evaluation/<int:judge_id>', methods=['POST'])
@login_required
def run_ai_judge(contest_id, judge_id):
    # Check permissions - only admin or assigned judges can trigger AI evaluation
    if not current_user.is_admin():
        flash('Solo los administradores pueden ejecutar evaluaciones de IA.', 'danger')
        return redirect(url_for('contest.detail', contest_id=contest_id))
    
    # Run the AI evaluation process
    result = run_ai_evaluation(contest_id, judge_id)
    
    if result['success']:
        flash(f"Evaluación de IA completada. {result['message']} Costo: ${result['cost']:.4f}", 'success')
    else:
        flash(f"Error al ejecutar evaluación de IA: {result['message']}", 'danger')
    
    # Return to submissions list
    return redirect(url_for('contest.list_submissions', contest_id=contest_id))

def calculate_contest_results(contest_id):
    """Calculates points and ranks for a contest if all judges have voted."""
    contest = db.session.get(Contest, contest_id)
    # Check if contest exists and is in evaluation phase
    if not contest or contest.status != 'evaluation':
        return False # Not ready or not found

    # Count how many *assigned* judges have submitted at least one vote for this contest
    judge_ids_with_votes = db.session.scalars(
        db.select(Vote.judge_id).distinct()
        .join(Vote.submission)
        .where(Submission.contest_id == contest.id)
    ).all()

    num_judges_voted = len(judge_ids_with_votes)
    # Get the required number of judges from the contest setting
    required_judges = contest.required_judges if contest.required_judges else 1

    # Check if the number of judges who voted meets the requirement
    if num_judges_voted < required_judges:
        return False # Not all required judges have voted

    print(f"Calculating results for Contest {contest.id} ('{contest.title}')...")

    # Fetch submissions for this contest
    submissions = contest.submissions.all()
    if not submissions:
        print(f"No submissions found for contest {contest.id}. Closing contest.")
        contest.status = 'closed'
        db.session.commit()
        return True # Nothing to rank, but process is complete
    
    # --- Calculation Steps --- 
    # 1. Reset points and rank for all submissions
    submission_points = {sub.id: 0 for sub in submissions}
    for sub in submissions:
        sub.total_points = 0
        sub.final_rank = None
    
    # 2. Calculate total points per submission
    points_map = {1: 3, 2: 2, 3: 1, 4: 0} # 1st=3, 2nd=2, 3rd=1, HM=0
    votes = db.session.scalars(
        db.select(Vote).join(Vote.submission).where(Submission.contest_id == contest.id)
    ).all()
    for vote in votes:
        if vote.place and vote.place in points_map:
            points = points_map[vote.place]
            if vote.submission_id in submission_points: # Ensure submission still exists
                submission_points[vote.submission_id] += points

    # 3. Update total_points on submission objects in the session
    for sub in submissions:
        sub.total_points = submission_points.get(sub.id, 0)

    # 4. Rank submissions based on points (handle ties using standard competition ranking)
    submissions.sort(key=lambda s: s.total_points, reverse=True) # Sort high to low
    current_rank = 0
    current_points = -1 # Initialize to impossible point value
    skip_ranks = 0
    for i, sub in enumerate(submissions):
        if sub.total_points != current_points: # New score, update rank
            current_rank += (1 + skip_ranks) # Jump rank based on ties
            current_points = sub.total_points
            skip_ranks = 0 # Reset tie counter
        else:
            skip_ranks += 1 # Same score as previous, count tie
        
        sub.final_rank = current_rank if sub.total_points > 0 else None # Assign rank only if points > 0

    # 5. Set contest status to closed
    contest.status = 'closed'
    db.session.commit()
    print(f"Results calculated and contest {contest.id} closed.")
    return True

# Add other contest routes here (e.g., list all, archive) 