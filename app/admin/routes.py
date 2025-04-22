from flask import render_template, flash, redirect, url_for, request, abort, session, current_app
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.forms import ContestForm, AddJudgeForm, AddAIJudgeForm, EditAIJudgeForm, ResetContestPasswordForm
from app.models import Contest, Submission, User, Vote, AIEvaluation, contest_judges
from app.decorators import admin_required
from app.config.ai_judge_params import AI_MODELS, AI_MODELS_RAW
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

@bp.route('/')
@login_required
@admin_required
def index():
    # Simple admin dashboard page
    return render_template('admin/index.html', title='Panel de Administración')

@bp.route('/contests')
@login_required
@admin_required
def list_contests():
    contests = db.session.scalars(db.select(Contest).order_by(Contest.start_date.desc())).all()
    current_time_utc = datetime.now(timezone.utc)
    return render_template('admin/list_contests.html', title='Gestionar Concursos', contests=contests, current_time_utc=current_time_utc, timezone=timezone)

@bp.route('/contests/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_contest():
    form = ContestForm()
    
    if form.validate_on_submit():
        # Get form data
        status = form.status.data
        contest_type = form.contest_type.data
        contest_password = form.contest_password.data if contest_type == 'private' else None
        
        # Create the contest
        contest = Contest(
            title=form.title.data,
            description=form.description.data,
            status=status,
            contest_type=contest_type,
            end_date=form.end_date.data,
            required_judges=form.required_judges.data
        )
        
        # Set password if private contest
        if contest_password:
            contest.set_password(contest_password)
            
        # Add to DB to get an ID
        db.session.add(contest)
        db.session.flush()  # Get ID without committing
        
        # Process judge assignments
        assigned_judge_ids = request.form.getlist('judges')
        
        if assigned_judge_ids:
            try:
                # Convert string IDs to integers
                assigned_judge_ids = [int(id) for id in assigned_judge_ids]
                judges = db.session.scalars(db.select(User).where(User.id.in_(assigned_judge_ids))).all()
                
                # Add judges to the contest via the association table
                for judge in judges:
                    # Get model for AI judges
                    ai_model = None
                    if judge.judge_type == 'ai':
                        ai_model = request.form.get(f'judge_model_{judge.id}')
                        if not ai_model:
                            flash(f'Debe seleccionar un modelo para el juez IA {judge.username}', 'danger')
                            available_models = [m for m in AI_MODELS_RAW if m.get('available', True)]
                            return render_template('admin/edit_contest.html', 
                                                  title='Crear Concurso', 
                                                  form=form, 
                                                  form_action=url_for('admin.create_contest'),
                                                  judge_is_ai=is_ai_judge,
                                                  ai_models=available_models)
                    
                    # Insert judge with model if AI, without if human
                    db.session.execute(db.insert(contest_judges).values(
                        user_id=judge.id, 
                        contest_id=contest.id,
                        ai_model=ai_model
                    ))
            except Exception as e:
                flash(f'Error al asignar jueces: {str(e)}', 'danger')
                db.session.rollback()
                available_models = [m for m in AI_MODELS_RAW if m.get('available', True)]
                return render_template('admin/edit_contest.html', 
                                     title='Crear Concurso', 
                                     form=form, 
                                     form_action=url_for('admin.create_contest'),
                                     judge_is_ai=is_ai_judge,
                                     ai_models=available_models)
        
        try:
            db.session.commit()
            flash(f'Concurso "{contest.title}" creado con éxito', 'success')
            return redirect(url_for('admin.list_contests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el concurso: {str(e)}', 'danger')
    
    # GET or form validation failure
    judge_model_map = {}
    if request.method == 'POST': # If form validation failed, repopulate map from form data
        assigned_judge_ids = request.form.getlist('judges')
        for judge_id_str in assigned_judge_ids:
            try:
                judge_id = int(judge_id_str)
                model = request.form.get(f'judge_model_{judge_id}')
                if model:
                    judge_model_map[judge_id] = model
            except ValueError:
                continue # Ignore non-integer judge IDs if any

    available_models = [m for m in AI_MODELS_RAW if m.get('available', True)]
    return render_template('admin/edit_contest.html', 
                         title='Crear Concurso', 
                         form=form, 
                         form_action=url_for('admin.create_contest'),
                         judge_is_ai=is_ai_judge,
                         judge_model_map=judge_model_map,
                         ai_models=available_models)

@bp.route('/contests/<int:contest_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    form = ContestForm(obj=contest)
    
    # Create a map of judge_id -> current ai_model
    judge_model_map = {}
    
    if request.method == 'GET':
        # Get current judge-model pairings from the database
        judge_model_results = db.session.execute(db.select(contest_judges.c.user_id, 
                                                         contest_judges.c.ai_model)
                                               .where(contest_judges.c.contest_id == contest.id)).all()
        
        # Create a map of judge_id -> ai_model
        for judge_id, ai_model in judge_model_results:
            if ai_model:  # Only include if model is not None
                judge_model_map[judge_id] = ai_model
                
        # Pre-populate judges multi-select field
        if contest.judges:
            form.judges.data = [judge.id for judge in contest.judges]
        else:
            form.judges.data = []
    
    if form.validate_on_submit():
        # Update basic contest data
        contest.title = form.title.data
        contest.description = form.description.data
        contest.status = form.status.data
        contest.contest_type = form.contest_type.data
        contest.end_date = form.end_date.data
        contest.required_judges = form.required_judges.data
        
        # Update password if private
        if contest.contest_type == 'private':
            if form.contest_password.data:
                contest.set_password(form.contest_password.data)
        else:
            contest.password_hash = None  # Clear password for public contests
        
        # Process judge assignments - first remove all existing judges
        try:
            # Delete all existing judge associations for this contest
            db.session.execute(db.delete(contest_judges).where(contest_judges.c.contest_id == contest.id))
            
            # Get the new judge assignments
            assigned_judge_ids = request.form.getlist('judges')
            
            if assigned_judge_ids:
                # Convert string IDs to integers
                assigned_judge_ids = [int(id) for id in assigned_judge_ids]
                judges = db.session.scalars(db.select(User).where(User.id.in_(assigned_judge_ids))).all()
                
                # Add judges to the contest via the association table
                for judge in judges:
                    # Get model for AI judges
                    ai_model = None
                    if judge.judge_type == 'ai':
                        ai_model = request.form.get(f'judge_model_{judge.id}')
                        if not ai_model:
                            flash(f'Debe seleccionar un modelo para el juez IA {judge.username}', 'danger')
                            # Get current judge models to repopulate the form
                            judge_model_results = db.session.execute(db.select(contest_judges.c.user_id, 
                                                                             contest_judges.c.ai_model)
                                                                   .where(contest_judges.c.contest_id == contest.id)).all()
                            for j_id, j_model in judge_model_results:
                                if j_model:
                                    judge_model_map[j_id] = j_model
                                    
                            available_models = [m for m in AI_MODELS_RAW if m.get('available', True)]
                            return render_template('admin/edit_contest.html',
                                                 title=f'Editar Concurso: {contest.title}',
                                                 form=form,
                                                 form_action=url_for('admin.edit_contest', contest_id=contest.id),
                                                 judge_is_ai=is_ai_judge,
                                                 judge_model_map=judge_model_map,
                                                 ai_models=available_models)
                    
                    # Insert judge with model if AI, without if human
                    db.session.execute(db.insert(contest_judges).values(
                        user_id=judge.id, 
                        contest_id=contest.id,
                        ai_model=ai_model
                    ))
            
            db.session.commit()
            flash(f'Concurso "{contest.title}" actualizado con éxito', 'success')
            return redirect(url_for('admin.list_contests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el concurso: {str(e)}', 'danger')
    
    # If validation failed or GET request
    # Reconstruct judge_model_map from form if POST request failed validation
    # Otherwise, use the map populated from DB in the GET request block
    if request.method == 'POST' and not form.validate_on_submit():
        judge_model_map = {} # Reset and rebuild from form
        assigned_judge_ids = request.form.getlist('judges')
        for judge_id_str in assigned_judge_ids:
            try:
                judge_id = int(judge_id_str)
                model = request.form.get(f'judge_model_{judge_id}')
                if model:
                    judge_model_map[judge_id] = model
            except ValueError:
                continue # Ignore non-integer judge IDs

    available_models = [m for m in AI_MODELS_RAW if m.get('available', True)]
    return render_template('admin/edit_contest.html',
                         title=f'Editar Concurso: {contest.title}',
                         form=form,
                         form_action=url_for('admin.edit_contest', contest_id=contest.id),
                         judge_is_ai=is_ai_judge,
                         judge_model_map=judge_model_map,
                         ai_models=available_models)

@bp.route('/contests/<int:contest_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # Delete contest
    db.session.delete(contest)
    db.session.commit()
    flash('Concurso eliminado exitosamente.', 'success')
    return redirect(url_for('admin.list_contests'))

# New route for resetting a contest password
@bp.route('/contests/<int:contest_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_contest_password(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # If contest is not private, redirect with an error
    if contest.contest_type != 'private':
        flash('Solo se puede cambiar la contraseña de concursos privados.', 'warning')
        return redirect(url_for('admin.list_contests'))
    
    form = ResetContestPasswordForm()
    
    if form.validate_on_submit():
        # Reset password
        contest.set_password(form.new_password.data)
        db.session.commit()
        
        # Clear any session access tokens for this contest
        for key in list(session.keys()):
            if key.startswith(f'contest_access_{contest_id}'):
                session.pop(key)
        
        flash('Contraseña del concurso cambiada exitosamente.', 'success')
        return redirect(url_for('admin.list_contests'))
    
    return render_template('admin/reset_contest_password.html', form=form, contest=contest)

@bp.route('/contests/<int:contest_id>/set_status', methods=['POST'])
@login_required
@admin_required
def set_contest_status(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        flash('Concurso no encontrado.', 'danger')
        return redirect(url_for('admin.list_contests'))

    new_status = request.form.get('new_status')
    allowed_statuses = ['open', 'evaluation', 'closed']

    if new_status and new_status in allowed_statuses:
        try:
            contest.status = new_status
            # Add logic here if certain transitions need checks (e.g., can't reopen a closed contest?)
            db.session.commit()
            flash(f'Estado del concurso "{contest.title}" cambiado a {new_status.capitalize()}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cambiar el estado: {e}', 'danger')
    else:
        flash('Estado inválido especificado.', 'danger')

    return redirect(url_for('admin.list_contests'))

@bp.route('/contests/<int:contest_id>/submissions')
@login_required
@admin_required
def list_submissions(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    submissions = db.session.scalars(
        db.select(Submission).where(Submission.contest_id == contest.id).order_by(Submission.submission_date.asc())
    ).all()
    return render_template('admin/list_submissions.html', title=f'Envíos para {contest.title}', contest=contest, submissions=submissions)

@bp.route('/submissions/<int:submission_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_submission(submission_id):
    submission = db.session.get(Submission, submission_id)
    if not submission:
        flash('Envío no encontrado.', 'danger')
        # Attempt to redirect back to a sensible default if contest_id is missing
        referer = request.headers.get("Referer")
        if referer:
             return redirect(referer)
        else:
            # Fallback if referer isn't available (less likely for POST)
            return redirect(url_for('admin.list_contests')) 

    contest_id = submission.contest_id  # Store contest_id for redirection

    try:
        # Delete associated votes first
        votes_to_delete = db.session.scalars(db.select(Vote).where(Vote.submission_id == submission.id)).all()
        for vote in votes_to_delete:
            db.session.delete(vote)
        
        # Now delete the submission
        db.session.delete(submission)
        db.session.commit()
        flash('Envío eliminado exitosamente.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error al eliminar el envío: {e}', 'danger')
        current_app.logger.error(f"Error deleting submission {submission_id}: {e}")

    return redirect(url_for('admin.list_submissions', contest_id=contest_id))

@bp.route('/users/add_judge', methods=['GET', 'POST'])
@login_required
@admin_required
def add_judge():
    form = AddJudgeForm()
    if form.validate_on_submit():
        judge_email = form.email.data or f'{form.username.data}@placeholder.email'

        # Check if username or (provided) email already exists
        existing_user = db.session.scalar(db.select(User).where(
            (User.username == form.username.data) |
            (User.email == judge_email)
        ))

        if existing_user:
            flash('Nombre de usuario o email ya existen.', 'danger')
        else:
            # Try creating the user
            try:
                user = User(
                    username=form.username.data,
                    email=judge_email,
                    role='judge'
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash(f'Juez "{user.username}" creado exitosamente.', 'success')
                # Redirect to the same page to allow adding another judge
                return redirect(url_for('admin.add_judge'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al crear juez: {e}', 'danger')
                # Let it fall through to render the template with the error

    # Render the template for GET request or if POST validation/creation failed
    return render_template('admin/add_judge.html', title='Agregar Nuevo Juez', form=form)

@bp.route('/users/ai_judges')
@login_required
@admin_required
def list_ai_judges():
    ai_judges = db.session.scalars(
        db.select(User).where(User.role == 'judge', User.judge_type == 'ai').order_by(User.username)
    ).all()
    return render_template('admin/list_ai_judges.html', title='Jueces de IA', ai_judges=ai_judges)

@bp.route('/users/add_ai_judge', methods=['GET', 'POST'])
@login_required
@admin_required
def add_ai_judge():
    form = AddAIJudgeForm()
    if form.validate_on_submit():
        # Try creating the AI judge
        try:
            # Create a password that's unusable for login (since this is an AI judge)
            import secrets
            random_password = secrets.token_hex(16)
            
            ai_judge = User(
                username=form.username.data,
                email=form.email.data,
                role='judge',
                judge_type='ai',
                ai_personality_prompt=form.ai_personality_prompt.data
            )
            ai_judge.set_password(random_password)
            db.session.add(ai_judge)
            db.session.commit()
            
            flash(f'Juez de IA "{ai_judge.username}" creado exitosamente.', 'success')
            return redirect(url_for('admin.list_ai_judges'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear juez de IA: {e}', 'danger')
    
    return render_template('admin/add_ai_judge.html', title='Agregar Juez de IA', form=form)

@bp.route('/users/edit_ai_judge/<int:judge_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ai_judge(judge_id):
    ai_judge = db.session.get(User, judge_id)
    if not ai_judge or ai_judge.role != 'judge' or ai_judge.judge_type != 'ai':
        abort(404)
    
    form = EditAIJudgeForm(obj=ai_judge)
    
    if form.validate_on_submit():
        try:
            # Update the AI judge
            ai_judge.ai_personality_prompt = form.ai_personality_prompt.data
            db.session.commit()
            
            flash(f'Juez de IA "{ai_judge.username}" actualizado exitosamente.', 'success')
            return redirect(url_for('admin.list_ai_judges'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar juez de IA: {e}', 'danger')
    
    return render_template('admin/edit_ai_judge.html', title='Editar Juez de IA', form=form, judge=ai_judge)

@bp.route('/users/delete_ai_judge/<int:judge_id>', methods=['POST'])
@login_required
@admin_required
def delete_ai_judge(judge_id):
    ai_judge = db.session.get(User, judge_id)
    if not ai_judge or ai_judge.role != 'judge' or ai_judge.judge_type != 'ai':
        abort(404)
    
    try:
        # Check if the judge has been assigned to any contests
        assigned_contests = ai_judge.judged_contests.all()
        if assigned_contests:
            contest_names = ', '.join([c.title for c in assigned_contests])
            flash(f'No se puede eliminar el juez porque está asignado a los siguientes concursos: {contest_names}', 'danger')
            return redirect(url_for('admin.list_ai_judges'))
        
        # Delete the judge
        db.session.delete(ai_judge)
        db.session.commit()
        flash(f'Juez de IA "{ai_judge.username}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar juez de IA: {e}', 'danger')
    
    return redirect(url_for('admin.list_ai_judges'))

@bp.route('/ai_evaluation_costs')
@login_required
@admin_required
def ai_evaluation_costs():
    """Display the costs of AI evaluations"""
    evaluations = AIEvaluation.query.order_by(AIEvaluation.timestamp.desc()).all()
    
    total_cost = sum(eval.cost for eval in evaluations) if evaluations else 0
    total_prompt_tokens = sum(eval.prompt_tokens for eval in evaluations) if evaluations else 0
    total_completion_tokens = sum(eval.completion_tokens for eval in evaluations) if evaluations else 0
    
    # Calculate costs by model
    model_costs = {}
    for eval in evaluations:
        if eval.ai_model not in model_costs:
            model_costs[eval.ai_model] = 0
        model_costs[eval.ai_model] += eval.cost
    
    # Prepare data for chart - convert to JSON-ready lists
    model_names = list(model_costs.keys())
    model_costs_values = [model_costs[model] for model in model_names]
    
    return render_template('admin/ai_evaluation_costs.html', 
                          evaluations=evaluations,
                          total_cost=total_cost,
                          total_prompt_tokens=total_prompt_tokens,
                          total_completion_tokens=total_completion_tokens,
                          model_names=model_names,
                          model_costs_values=model_costs_values)

@bp.route('/ai_evaluation/<int:evaluation_id>')
@login_required
@admin_required
def view_ai_evaluation(evaluation_id):
    """Display a specific AI evaluation with full details"""
    evaluation = db.session.get(AIEvaluation, evaluation_id)
    if not evaluation:
        flash('Evaluación no encontrada', 'danger')
        return redirect(url_for('admin.ai_evaluation_costs'))
    
    return render_template('admin/view_ai_evaluation.html',
                          title='Detalles de Evaluación de IA',
                          evaluation=evaluation)

# Add route for listing users later maybe
# @bp.route('/users')
# @login_required
# @admin_required
# def list_users():
#     pass 

# Helper function to check if a user is an AI judge
def is_ai_judge(user_id):
    user = db.session.get(User, user_id)
    return user and user.judge_type == 'ai' 