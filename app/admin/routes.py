from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required
from app import db
from app.admin import bp
from app.admin.forms import ContestForm, AddJudgeForm
from app.models import Contest, Submission, User
from app.decorators import admin_required

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
    return render_template('admin/list_contests.html', title='Gestionar Concursos', contests=contests)

@bp.route('/contests/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_contest():
    form = ContestForm()
    if form.validate_on_submit():
        contest = Contest(
            title=form.title.data,
            description=form.description.data,
            end_date=form.end_date.data,
            required_judges=form.required_judges.data,
            contest_type=form.contest_type.data,
            anonymous_submissions=form.anonymous_submissions.data,
            status=form.status.data
        )
        if form.contest_type.data == 'private' and form.contest_password.data:
            contest.set_password(form.contest_password.data)
        else:
            contest.password_hash = None # Ensure public doesn't have password
        
        # Handle judge assignments
        assigned_judge_ids = form.judges.data # Returns list of selected IDs
        contest.judges = db.session.scalars(db.select(User).where(User.id.in_(assigned_judge_ids))).all()
        
        db.session.add(contest)
        db.session.commit()
        flash('Concurso creado exitosamente.', 'success')
        return redirect(url_for('admin.list_contests'))
    return render_template('admin/edit_contest.html', title='Crear Concurso', form=form, form_action=url_for('admin.create_contest'))

@bp.route('/contests/<int:contest_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    form = ContestForm(obj=contest)
    
    # Pre-populate judges multi-select field
    if request.method == 'GET':
        form.judges.data = [judge.id for judge in contest.judges]
    
    if form.validate_on_submit():
        # Update fields from form
        contest.title = form.title.data
        contest.description = form.description.data
        contest.end_date = form.end_date.data
        contest.required_judges = form.required_judges.data
        contest.contest_type = form.contest_type.data
        contest.anonymous_submissions = form.anonymous_submissions.data
        contest.status = form.status.data
        
        if form.contest_type.data == 'private':
            if form.contest_password.data:
                contest.set_password(form.contest_password.data)
        else:
            contest.password_hash = None # Remove password if changed to public

        # Handle judge assignments update
        assigned_judge_ids = form.judges.data
        contest.judges = db.session.scalars(db.select(User).where(User.id.in_(assigned_judge_ids))).all()

        db.session.commit()
        flash('Concurso actualizado exitosamente.', 'success')
        return redirect(url_for('admin.list_contests'))
    
    form.contest_password.data = '' 
    
    return render_template('admin/edit_contest.html', title='Editar Concurso', form=form, contest=contest, form_action=url_for('admin.edit_contest', contest_id=contest.id))

@bp.route('/contests/<int:contest_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_contest(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    
    # TODO: Add cascading delete or check for submissions before deleting?
    # For now, directly delete the contest.
    db.session.delete(contest)
    db.session.commit()
    flash('Concurso eliminado exitosamente.', 'success')
    return redirect(url_for('admin.list_contests'))

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

# Add route for listing users later maybe
# @bp.route('/users')
# @login_required
# @admin_required
# def list_users():
#     pass 