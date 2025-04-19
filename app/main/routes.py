from flask import render_template, url_for, redirect, request, flash
from flask_login import current_user
from app.main import bp
from app.models import Contest, User, Submission, Entry, Vote, UserRole, JudgeType # Import Enums
from app import db
# Import the whole module or specific classes like date
# from datetime import datetime # Old import
import datetime # Import the module
# Use main forms
from app.main.forms import RegistrationForm, ProfileForm

@bp.route('/')
@bp.route('/index')
def index():
    current_time = datetime.datetime.utcnow()
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
    if current_user.is_authenticated and current_user.role == UserRole.JUDGE: # Use Enum
        judge_assigned_evaluations = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .where(Contest.judges.any(User.id == current_user.id))
            .order_by(Contest.end_date.asc())
        ).all()

    return render_template('main/index.html', 
                           title='Inicio', 
                           active_contests=active_contests,
                           closed_contests=closed_contests,
                           judge_assigned_evaluations=judge_assigned_evaluations,
                           Submission=Submission) # Pass Submission model

# New Route for listing all contests by status
@bp.route('/contests')
def list_contests():
    now = datetime.datetime.utcnow()
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
    if current_user.is_authenticated and current_user.role == UserRole.JUDGE: # Use Enum
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

# --- New Public Registration Route --- 
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Ya has iniciado sesión.', 'info')
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    # Ensure choices are set (might be redundant if form does it, but safe)
    form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole if role != UserRole.ADMIN]
    
    if form.validate_on_submit():
        # Convert form string value ('user' or 'judge') to Enum member
        try:
            selected_role_enum = UserRole(form.role.data)
        except ValueError:
             flash('Rol inválido seleccionado.', 'danger')
             return render_template('main/register.html', title='Registrar', form=form)
        
        # selected_judge_type = form.judge_type.data # This field is commented out in the form
        # ai_model_id = form.ai_model_id.data if selected_judge_type == JudgeType.AI else None
        # ai_prompt = form.ai_personality_prompt.data if selected_judge_type == JudgeType.AI else None
        
        judge_type_to_save = None
        ai_model_id_to_save = None
        ai_prompt_to_save = None
        
        # Public registration only allows User or Judge
        # If Judge, force type to HUMAN
        if selected_role_enum == UserRole.JUDGE:
            judge_type_to_save = JudgeType.HUMAN # Force human for public registration
            # ai_model_id_to_save = None # Already None
            # ai_prompt_to_save = None # Already None
        elif selected_role_enum == UserRole.USER:
            judge_type_to_save = None # Users don't have a judge type
            # ai_model_id_to_save = None
            # ai_prompt_to_save = None
        else:
            # This case should ideally be caught by form validation, but as a safeguard:
            flash('Rol no válido para registro público.', 'warning')
            return render_template('main/register.html', title='Registrar', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=selected_role_enum, # Use the Enum member
            judge_type=judge_type_to_save, # Set based on logic above (HUMAN or None)
            ai_model_id=ai_model_id_to_save, # Always None for public reg
            ai_personality_prompt=ai_prompt_to_save # Always None for public reg
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, ahora eres un usuario registrado!', 'success')
        return redirect(url_for('auth.login'))
        
    # Handle GET request (ensure choices are set)
    elif request.method == 'GET':
         form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole if role != UserRole.ADMIN]
        
    return render_template('main/register.html', title='Registrar', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if current_user.is_authenticated:
        # Pass current user's username/email to form for validation check
        form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
        if form.validate_on_submit():
            # Update user data, but DO NOT allow changing role or judge_type here
            current_user.username = form.username.data
            current_user.email = form.email.data
            if form.password.data:
                current_user.set_password(form.password.data)
            db.session.commit()
            flash('Tu perfil ha sido actualizado.', 'success')
            return redirect(url_for('main.profile'))
        elif request.method == 'GET':
            # Pre-populate form fields for display
            form.username.data = current_user.username
            form.email.data = current_user.email
            # Don't pre-fill password fields
        return render_template('main/profile.html', title='Perfil', form=form)
    else:
        flash('No has iniciado sesión.', 'warning')
        return redirect(url_for('auth.login'))

@bp.route('/contest/<int:contest_id>')
def contest_detail(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    # Fetch Submissions, not Entries, for this contest view
    submissions = db.session.scalars(db.select(Submission).filter_by(contest_id=contest_id)).all()
    
    user_has_voted_in_contest = False # Check if judge has voted on *any* submission
    if current_user.is_authenticated:
        # Check if the current user has any vote associated with this contest_id
        existing_vote_count = db.session.scalar(
            db.select(db.func.count(Vote.id)).where(
                Vote.judge_id == current_user.id,
                Vote.contest_id == contest_id
            )
        )
        user_has_voted_in_contest = existing_vote_count > 0

    # Use naive UTC datetime for comparison consistency with DB retrieval
    now_utc_naive = datetime.datetime.utcnow() 
    can_vote = contest.status == 'open' and now_utc_naive >= contest.start_date and now_utc_naive <= contest.end_date
    # Determine if voting should be blocked for this user
    # Voting is blocked if they can't vote OR if they have already voted in this contest
    block_voting = not can_vote or user_has_voted_in_contest

    # Sort submissions (e.g., by title or date) if needed
    submissions.sort(key=lambda x: x.submission_date) 

    return render_template(
        'contest/detail.html', # Correct path to the template 
        title=contest.title, 
        contest=contest, 
        submissions=submissions, # Pass submissions 
        can_vote=can_vote, # Can voting happen in general?
        has_voted=user_has_voted_in_contest, # Has *this specific user* voted?
        block_voting=block_voting # Should vote buttons be disabled?
        # user_vote_entry_id=user_vote.entry_id if has_voted else None # Removed
    )

@bp.route('/vote/<int:contest_id>/<int:submission_id>', methods=['POST'])
def vote(contest_id, submission_id): # Takes submission_id now
    if not current_user.is_authenticated or current_user.role != UserRole.JUDGE: # Use Enum
        flash('Solo los jueces autenticados pueden votar.', 'warning')
        return redirect(url_for('main.contest_detail', contest_id=contest_id))
        
    contest = Contest.query.get_or_404(contest_id)
    submission = Submission.query.get_or_404(submission_id)
    
    # Check contest status and dates using naive UTC datetime
    now_utc_naive = datetime.datetime.utcnow()
    if contest.status != 'open' or not (now_utc_naive >= contest.start_date and now_utc_naive <= contest.end_date):
        flash('Este concurso no está abierto para votación.', 'warning')
        return redirect(url_for('main.contest_detail', contest_id=contest_id))
    
    # Check if user has already voted ON THIS SUBMISSION
    existing_vote = db.session.scalar(
        db.select(Vote).where(
            Vote.judge_id == current_user.id,
            Vote.submission_id == submission_id # Check against submission_id
        )
    )
    if existing_vote:
        flash('Ya has votado por esta obra.', 'warning')
        return redirect(url_for('main.contest_detail', contest_id=contest_id))

    # --- Process vote form data (assuming form fields: place, comment) ---
    # Example: Get data from request.form - NEED A FORM HERE ideally
    vote_place = request.form.get('place') # Get place from form data
    vote_comment = request.form.get('comment') # Get comment from form data

    # Add validation for vote_place (e.g., must be 1, 2, 3, or 4)
    try:
        place_int = int(vote_place) if vote_place else None
        if place_int is not None and place_int not in [1, 2, 3, 4]:
             raise ValueError("Lugar inválido.")
    except (ValueError, TypeError):
        flash('Por favor, selecciona un lugar válido (1, 2, 3, o 4 para Mención Honorífica).', 'danger')
        return redirect(url_for('main.contest_detail', contest_id=contest_id))
    
    # Record the vote using submission_id
    new_vote = Vote(
        judge_id=current_user.id, 
        contest_id=contest_id, 
        submission_id=submission_id, # Use submission_id
        place=place_int, # Store integer place
        comment=vote_comment
    )
    db.session.add(new_vote)
    db.session.commit()
    flash('¡Tu voto ha sido registrado!', 'success')
    return redirect(url_for('main.contest_detail', contest_id=contest_id))

# Add other main routes here (e.g., about page) 