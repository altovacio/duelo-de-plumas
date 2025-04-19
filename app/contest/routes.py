from flask import render_template, flash, redirect, url_for, abort, request
from flask_login import current_user, login_required # Added login_required
from app import db
from app.contest import bp
from app.contest.forms import SubmissionForm, ContestEvaluationForm, SubmissionRankForm
from app.models import Contest, Submission, Vote, User, AIEvaluationRun # Added AIEvaluationRun
# Standardize datetime import
import datetime # New
from app.decorators import judge_required, admin_required
from sqlalchemy import func, distinct
from wtforms.validators import ValidationError
from sqlalchemy.orm import joinedload
# Import the AI service function
from app.services.ai_judge_service import run_ai_judge_evaluation

@bp.route('/<int:contest_id>', methods=['GET', 'POST'])
def detail(contest_id):
    print(f"--- Entering contest.detail route for contest_id: {contest_id} ---") # Earliest possible debug point
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404) # Contest not found

    # Always create a form object, regardless of contest status
    form = SubmissionForm()
    
    # Check if contest is public or if user needs password for private contest (implement later)
    if contest.contest_type == 'private':
        # TODO: Add password check logic here for private contests
        flash('Los concursos privados aún no están implementados.', 'warning')
        # For now, maybe redirect or show limited info
        # return redirect(url_for('main.index'))
        pass # Allow access for now during development

    # --- DEBUGGING is_open --- 
    # Use datetime module path
    now_utc_naive = datetime.datetime.utcnow() # Use naive UTC time 
    print(f"DEBUG [detail route]: contest.id = {contest.id}")
    print(f"DEBUG [detail route]: contest.status = {contest.status!r} (Type: {type(contest.status)})")
    print(f"DEBUG [detail route]: contest.end_date = {contest.end_date!r} (Type: {type(contest.end_date)})")
    print(f"DEBUG [detail route]: now_utc_naive = {now_utc_naive!r} (Type: {type(now_utc_naive)})")
    status_check = (contest.status == 'open')
    date_check = (contest.end_date > now_utc_naive)
    print(f"DEBUG [detail route]: Status check (== 'open') = {status_check}")
    print(f"DEBUG [detail route]: Date check (> now) = {date_check}")
    # --- END DEBUGGING ---
    
    # Consider a contest open if its status is 'open', regardless of date
    is_open = status_check  # Removed the date_check condition
    is_evaluation = (contest.status == 'evaluation')
    is_closed = (contest.status == 'closed')
    
    print(f"DEBUG: Final is_open = {is_open}, is_evaluation = {is_evaluation}, is_closed = {is_closed}")
    
    submissions_list = []
    votes_list = []
    votes_by_submission = {}

    # Process the form if submitted and contest is open
    if is_open and form.validate_on_submit():
        submission = Submission(
            author_name=form.author_name.data,
            title=form.title.data,
            text_content=form.text_content.data,
            contest_id=contest.id
        )
        db.session.add(submission)
        db.session.commit()
        flash('Tu texto ha sido enviado exitosamente.', 'success')
        return redirect(url_for('contest.detail', contest_id=contest.id))

    # Process the form submission from the manual form
    if request.method == 'POST' and contest.status == 'open':
        # Check if required fields are present
        author_name = request.form.get('author_name')
        title = request.form.get('title')
        text_content = request.form.get('text_content')
        
        # Validate the form data manually
        errors = []
        if not author_name:
            errors.append('El nombre del autor es obligatorio.')
        if not title:
            errors.append('El título es obligatorio.')
        if not text_content:
            errors.append('El contenido del texto es obligatorio.')
            
        # If no errors, create a new submission
        if not errors:
            submission = Submission(
                author_name=author_name,
                title=title,
                text_content=text_content,
                contest_id=contest.id
            )
            db.session.add(submission)
            db.session.commit()
            flash('Tu texto ha sido enviado exitosamente.', 'success')
            return redirect(url_for('contest.detail', contest_id=contest.id))
        else:
            # Show errors
            for error in errors:
                flash(error, 'danger')
                
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
                           is_evaluation=is_evaluation,
                           is_closed=is_closed,
                           current_time=datetime.datetime.utcnow(),
                           submissions_list=submissions_list,
                           votes_by_submission=votes_by_submission if is_closed else {}
                          )

# --- ALL OTHER ROUTES TEMPORARILY COMMENTED OUT --- 
@bp.route('/<int:contest_id>/submissions')
@login_required
@judge_required
def list_submissions(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
        
    # Check if user is assigned as judge to this contest
    assigned_judge = None
    if current_user.role == 'judge':
        assigned_judge = current_user
        # Check if this judge is assigned to this contest
        if not current_user.is_admin() and contest not in current_user.judging_contests:
            flash('No estás asignado como juez para este concurso.', 'danger')
            return redirect(url_for('main.index'))
    
    # Get all submissions for this contest
    submissions = db.session.scalars(
        db.select(Submission)
        .where(Submission.contest_id == contest_id)
        .order_by(Submission.submission_date)
    ).all()
    
    # Check if evaluation can be performed (contest in evaluation status)
    can_evaluate = contest.status == 'evaluation'
    
    # See if this judge has already voted
    already_voted = False
    if assigned_judge:
        vote_count = db.session.scalar(
            db.select(func.count())
            .select_from(Vote)
            .join(Submission)
            .where(
                Vote.judge_id == current_user.id,
                Submission.contest_id == contest_id
            )
        )
        already_voted = vote_count > 0

    return render_template('contest/list_submissions.html',
                          title=f"Envíos para {contest.title}",
                          contest=contest,
                          submissions=submissions,
                          can_evaluate=can_evaluate,
                          already_voted=already_voted,
                          assigned_judge=assigned_judge)

@bp.route('/<int:contest_id>/evaluate', methods=['GET'])
@login_required
def evaluate_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # Check if contest is in evaluation phase
    if contest.status != 'evaluation':
        flash('Este concurso no está abierto para evaluación en este momento.', 'warning')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    
    # Determine assigned judge
    assigned_judge = None
    if current_user.role == 'judge':
        assigned_judge = current_user
        # Check if judge is assigned to this contest
        if not current_user.is_admin() and contest not in current_user.judging_contests:
            flash('No estás asignado como juez para este concurso.', 'danger')
            return redirect(url_for('main.index'))
    
    # Check if user has permission to evaluate
    if not current_user.is_admin() and current_user.role != 'judge':
        flash('No tienes permiso para evaluar concursos.', 'danger')
        return redirect(url_for('contest.detail', contest_id=contest_id))
    
    # Get all submissions for this contest
    submissions = db.session.scalars(
        db.select(Submission)
        .where(Submission.contest_id == contest_id)
        .order_by(Submission.submission_date)
    ).all()
    
    # Check if AI judge is trying to evaluate
    if assigned_judge and assigned_judge.judge_type == 'AI':
        return render_template('contest/ai_evaluation_form.html',
                              title=f"Evaluación IA para {contest.title}",
                              contest=contest,
                              judge=assigned_judge)

    # Create form with subforms for each submission
    form = ContestEvaluationForm()
    
    # Add a subform for each submission
    for sub in submissions:
        sub_form = SubmissionRankForm()
        sub_form.submission_id.data = sub.id
        form.submissions.append_entry(sub_form)
    
    return render_template('contest/evaluate_contest.html',
                          title=f"Evaluar {contest.title}",
                          contest=contest,
                          submissions=submissions,
                          form=form,
                          assigned_judge=assigned_judge)

@bp.route('/<int:contest_id>/submit_human_evaluation', methods=['POST'])
@login_required
def submit_human_evaluation(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # Check if contest is in evaluation phase
    if contest.status != 'evaluation':
        flash('Este concurso no está abierto para evaluación en este momento.', 'warning')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    
    # Check if user has permission to evaluate (judge or admin)
    if not current_user.is_admin() and current_user.role != 'judge':
        flash('No tienes permiso para evaluar concursos.', 'danger')
        return redirect(url_for('contest.detail', contest_id=contest_id))
    
    # If judge, check if assigned to this contest
    if current_user.role == 'judge' and not current_user.is_admin():
        if contest not in current_user.judging_contests:
            flash('No estás asignado como juez para este concurso.', 'danger')
            return redirect(url_for('main.index'))
    
    form = ContestEvaluationForm()
    
    # Check if form is valid
    if form.validate_on_submit():
        # First, check that selection is valid (exactly one 1st, one 2nd, one 3rd)
        place_counts = {1: 0, 2: 0, 3: 0}
        
        # Get the total number of submissions
        submission_count = db.session.scalar(
            db.select(func.count())
            .select_from(Submission)
            .where(Submission.contest_id == contest_id)
        )
        
        # Count selections by place
        for sub_form in form.submissions:
            if sub_form.place.data in [1, 2, 3]:
                place_counts[sub_form.place.data] += 1
        
        # Validate place requirements - we need at least 3 submissions to require all places
        if submission_count >= 3:
            # Need exactly one 1st, one 2nd, one 3rd
            if place_counts[1] != 1 or place_counts[2] != 1 or place_counts[3] != 1:
                flash('Evaluación inválida. Debes asignar exactamente un 1er, un 2do y un 3er lugar.', 'danger')
                return redirect(url_for('contest.evaluate_contest', contest_id=contest_id))
        elif submission_count == 2:
            # Need exactly one 1st, one 2nd
            if place_counts[1] != 1 or place_counts[2] != 1:
                flash('Evaluación inválida. Debes asignar exactamente un 1er y un 2do lugar.', 'danger')
                return redirect(url_for('contest.evaluate_contest', contest_id=contest_id))
        elif submission_count == 1:
            # Need exactly one 1st
            if place_counts[1] != 1:
                flash('Evaluación inválida. Debes asignar el 1er lugar.', 'danger')
                return redirect(url_for('contest.evaluate_contest', contest_id=contest_id))
        
        # Delete any existing votes by this judge for this contest
        db.session.execute(
            db.delete(Vote)
            .where(
                Vote.judge_id == current_user.id,
                Vote.submission_id.in_(
                    db.select(Submission.id)
                    .where(Submission.contest_id == contest_id)
                )
            )
        )
        
        # Add new votes
        for sub_form in form.submissions:
            if sub_form.place.data > 0:  # Only record votes with actual place assignments
                points = 0
                if sub_form.place.data == 1:
                    points = 5
                elif sub_form.place.data == 2:
                    points = 3
                elif sub_form.place.data == 3:
                    points = 1
                elif sub_form.place.data == 4:  # Honorable mention
                    points = 0
                
                vote = Vote(
                    judge_id=current_user.id,
                    submission_id=sub_form.submission_id.data,
                    place=sub_form.place.data,
                    points=points,
                    comment=sub_form.comment.data
                )
                db.session.add(vote)
        
        db.session.commit()
        
        # Check if all judges have voted and update contest status if needed
        calculate_contest_results(contest_id)
        
        flash('Tu evaluación ha sido registrada exitosamente.', 'success')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en formulario: {error}', 'danger')
        
        return redirect(url_for('contest.evaluate_contest', contest_id=contest_id))

@bp.route('/<int:contest_id>/run_ai_evaluation/<int:judge_id>', methods=['POST'])
@login_required
@admin_required 
def trigger_ai_evaluation(contest_id, judge_id):
    # Check if contest exists
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # Check if judge exists and is AI type
    judge = db.session.get(User, judge_id)
    if not judge or judge.role != 'judge' or judge.judge_type != 'AI':
        flash('Juez IA no válido.', 'danger')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    
    # Check if contest is in evaluation phase
    if contest.status != 'evaluation':
        flash('Este concurso no está abierto para evaluación.', 'warning')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    
    # Get all submissions
    submissions = db.session.scalars(
        db.select(Submission)
        .where(Submission.contest_id == contest_id)
        .order_by(Submission.submission_date)
    ).all()
    
    # Check if we have enough submissions to evaluate
    if len(submissions) < 1:
        flash('No hay suficientes envíos para evaluar.', 'warning')
        return redirect(url_for('contest.list_submissions', contest_id=contest_id))
    
    # Create a record of this AI evaluation run
    ai_run = AIEvaluationRun(
        judge_id=judge_id,
        contest_id=contest_id,
        status='pending',
        started_at=datetime.datetime.utcnow()
    )
    db.session.add(ai_run)
    db.session.commit()
    
    try:
        # Call the AI judge service
        run_ai_judge_evaluation(contest_id, judge_id, ai_run.id)
        
        # Check if all judges have voted and update contest status if needed
        calculate_contest_results(contest_id)
        
        flash('Evaluación IA completada exitosamente.', 'success')
    except Exception as e:
        flash(f'Error en evaluación IA: {str(e)}', 'danger')
        # Update run status
        ai_run.status = 'error'
        ai_run.error_message = str(e)
        ai_run.completed_at = datetime.datetime.utcnow()
        db.session.commit()
    
    return redirect(url_for('contest.list_submissions', contest_id=contest_id))

def calculate_contest_results(contest_id):
    """Calculate final results for a contest if all judges have voted"""
    
    # Check if contest exists
    contest = db.session.get(Contest, contest_id)
    if not contest:
        return False
    
    # Check if contest is in evaluation phase
    if contest.status != 'evaluation':
        return False
    
    # Get count of assigned judges
    assigned_judge_count = len(contest.judges)
    
    # Get count of judges who have voted
    votes_by_judge = db.session.scalar(
        db.select(func.count(distinct(Vote.judge_id)))
        .join(Vote.submission)
        .where(Submission.contest_id == contest_id)
    )
    
    # If not all judges have voted, don't calculate results yet
    if votes_by_judge < assigned_judge_count:
        return False
    
    # All judges have voted - calculate and update results
    
    # Get all submissions
    submissions = db.session.scalars(
        db.select(Submission)
        .where(Submission.contest_id == contest_id)
    ).all()
    
    # Calculate total points for each submission
    for submission in submissions:
        votes = db.session.scalars(
            db.select(Vote)
            .where(Vote.submission_id == submission.id)
        ).all()
        
        # Sum points
        total_points = sum(vote.points for vote in votes)
        submission.total_points = total_points
    
    # Sort submissions by points to determine ranks
    sorted_submissions = sorted(submissions, key=lambda s: s.total_points, reverse=True)
    
    # Assign final ranks - handle ties by giving same rank
    current_rank = 1
    current_points = None
    
    for i, submission in enumerate(sorted_submissions):
        if submission.total_points != current_points:
            current_rank = i + 1
            current_points = submission.total_points
        
        # Only assign ranks 1-3 and HM=4
        if current_rank <= 4:
            submission.final_rank = current_rank
        else:
            submission.final_rank = None
    
    # Update contest status to closed
    contest.status = 'closed'
    
    # Commit all changes
    db.session.commit()
    
    return True

# Add other contest routes here (e.g., list all, archive) 