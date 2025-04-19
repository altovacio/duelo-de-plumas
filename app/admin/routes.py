from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.forms import ContestForm, UserForm, EntryForm, DeleteForm
from app.models import Contest, Submission, User, UserRole, JudgeType, Entry, Vote
from app.decorators import admin_required
from werkzeug.utils import secure_filename
import os
from config import Config

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
    delete_form = DeleteForm()
    return render_template('admin/list_contests.html', title='Gestionar Concursos', contests=contests, delete_form=delete_form)

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

@bp.route('/users')
@login_required
@admin_required
def list_users():
    users = db.session.scalars(db.select(User).order_by(User.username)).all()
    return render_template('admin/list_users.html', title='Gestionar Usuarios', users=users)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    # Manually set choices using Enum values and names
    form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
    form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]

    if form.validate_on_submit():
        # --- DEBUGGING --- 
        print(f"DEBUG [add_user]: Submitted form.role.data = {form.role.data!r} (Type: {type(form.role.data)})")
        print(f"DEBUG [add_user]: Submitted form.judge_type.data = {form.judge_type.data!r} (Type: {type(form.judge_type.data)})")
        # --- END DEBUGGING ---
        
        # Convert form string data back to Enum members
        try:
            # Ensure data is treated as string before Enum conversion
            role_data_str = str(form.role.data)
            judge_type_data_str = str(form.judge_type.data) if form.judge_type.data else None 
            
            print(f"DEBUG [add_user]: Converting role_data_str = {role_data_str!r}") # More debug
            selected_role_enum = UserRole(role_data_str)
            
            print(f"DEBUG [add_user]: Converting judge_type_data_str = {judge_type_data_str!r}") # More debug
            selected_judge_type_enum = JudgeType(judge_type_data_str) if judge_type_data_str else None
            
        except ValueError as e:
            flash(f"Valor inválido seleccionado: {e}", "danger")
            # Reset choices on error return
            form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
            form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]
            return render_template('admin/user_form.html', title='Añadir Usuario', form=form, form_action=url_for('admin.add_user'))

        judge_type_to_save = None
        ai_model_id_to_save = None
        ai_prompt_to_save = None

        # Only set judge_type if role is JUDGE
        if selected_role_enum == UserRole.JUDGE:
            judge_type_to_save = selected_judge_type_enum
            if judge_type_to_save == JudgeType.AI:
                ai_model_id_to_save = form.ai_model_id.data
                ai_prompt_to_save = form.ai_personality_prompt.data
            # Ensure AI fields are None if type is HUMAN
            elif judge_type_to_save == JudgeType.HUMAN:
                 ai_model_id_to_save = None
                 ai_prompt_to_save = None
            # Handle case where judge role is selected but no judge type (shouldn't happen with validation)
            elif judge_type_to_save is None:
                 flash("Se seleccionó el rol de Juez pero no se especificó el tipo (Humano/IA).", "warning")
                 # Optionally default to HUMAN or return form
                 judge_type_to_save = JudgeType.HUMAN # Defaulting to Human
                 ai_model_id_to_save = None
                 ai_prompt_to_save = None

        # Ensure judge fields are None if role is not JUDGE
        if selected_role_enum != UserRole.JUDGE:
             judge_type_to_save = None
             ai_model_id_to_save = None
             ai_prompt_to_save = None

        # Check for duplicate username/email before creating
        existing_user_by_name = db.session.scalar(db.select(User).where(User.username == form.username.data))
        existing_user_by_email = db.session.scalar(db.select(User).where(User.email == form.email.data))
        if existing_user_by_name:
             flash('Este nombre de usuario ya está en uso.', 'warning')
             return render_template('admin/user_form.html', title='Añadir Usuario', form=form, form_action=url_for('admin.add_user'))
        if existing_user_by_email:
             flash('Esta dirección de email ya está registrada.', 'warning')
             return render_template('admin/user_form.html', title='Añadir Usuario', form=form, form_action=url_for('admin.add_user'))

        user = User(
            username=form.username.data,
            email=form.email.data,
            role=selected_role_enum, # Store the Enum member
            judge_type=judge_type_to_save, # Store the Enum member or None
            ai_model_id=ai_model_id_to_save,
            ai_personality_prompt=ai_prompt_to_save
        )
        # Password is required for adding user (form validation should handle this)
        if not form.password.data:
             flash('La contraseña es obligatoria para nuevos usuarios.', 'danger')
             return render_template('admin/user_form.html', title='Añadir Usuario', form=form, form_action=url_for('admin.add_user'))

        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {e}', 'danger')

    # Ensure choices are set for the initial GET request too
    elif request.method == 'GET':
         form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
         form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]

    return render_template('admin/user_form.html', title='Añadir Usuario', form=form, form_action=url_for('admin.add_user'))

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    # Pass current user object and original values for validation checks
    form = UserForm(obj=user, original_username=user.username, original_email=user.email)
    # Manually set choices using Enum values and names
    form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
    form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]

    if form.validate_on_submit():
        try:
            # Convert form string data back to Enum members
            selected_role_enum = UserRole(form.role.data)
            selected_judge_type_enum = JudgeType(form.judge_type.data) if form.judge_type.data else None

            # Check for duplicate username/email ONLY if they changed
            if form.username.data != user.username:
                 existing_user_by_name = db.session.scalar(db.select(User).where(User.username == form.username.data))
                 if existing_user_by_name:
                      flash('Este nombre de usuario ya está en uso.', 'warning')
                      # Need to reset choices on error return
                      form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
                      form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]
                      return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user, form_action=url_for('admin.edit_user', user_id=user.id))
            if form.email.data != user.email:
                 existing_user_by_email = db.session.scalar(db.select(User).where(User.email == form.email.data))
                 if existing_user_by_email:
                      flash('Esta dirección de email ya está registrada.', 'warning')
                      form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
                      form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]
                      return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user, form_action=url_for('admin.edit_user', user_id=user.id))


            user.username = form.username.data
            user.email = form.email.data
            user.role = selected_role_enum

            # Reset judge-specific fields first
            user.judge_type = None
            user.ai_model_id = None
            user.ai_personality_prompt = None

            # Set judge-specific fields only if role is JUDGE
            if selected_role_enum == UserRole.JUDGE:
                user.judge_type = selected_judge_type_enum
                if user.judge_type == JudgeType.AI:
                    user.ai_model_id = form.ai_model_id.data
                    user.ai_personality_prompt = form.ai_personality_prompt.data
                # Handle case where judge role is selected but no judge type (shouldn't happen with validation)
                elif user.judge_type is None:
                     flash("Se seleccionó el rol de Juez pero no se especificó el tipo (Humano/IA).", "warning")
                     user.judge_type = JudgeType.HUMAN # Defaulting to Human? Check logic
                     user.ai_model_id = None
                     user.ai_personality_prompt = None
                # Ensure AI fields are None if type is HUMAN (handled by reset above)

            if form.password.data:
                user.set_password(form.password.data)

            db.session.commit()
            flash(f'Usuario "{user.username}" actualizado exitosamente.', 'success')
            return redirect(url_for('admin.list_users'))
        except ValueError as e:
             flash(f"Valor inválido seleccionado: {e}", "danger")
             # Need to reset choices on error return
             form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
             form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {e}', 'danger')

    # Pre-populate form on GET request, ensuring Enum values are used for selects
    elif request.method == 'GET':
        # WTForms obj=user handles most fields
        # Set select field data explicitly using the Enum *value*
        form.role.data = user.role.value if user.role else None
        form.judge_type.data = user.judge_type.value if user.judge_type else None
        form.password.data = "" # Clear password fields
        form.password2.data = ""

    # Ensure choices are set for GET request rendering too
    form.role.choices = [(role.value, role.name.capitalize()) for role in UserRole]
    form.judge_type.choices = [(jtype.value, jtype.name.capitalize()) for jtype in JudgeType]

    return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user, form_action=url_for('admin.edit_user', user_id=user.id))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user.id == current_user.id:
         flash('No puedes eliminar tu propia cuenta.', 'danger')
         return redirect(url_for('admin.list_users'))
    # Consider implications: delete related votes, entries? For now, just delete user.
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect(url_for('admin.list_users'))

@bp.route('/contests/<int:contest_id>/entries')
@login_required
@admin_required
def list_entries(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    entries = db.session.scalars(
        db.select(Entry).where(Entry.contest_id == contest.id).order_by(Entry.title.asc())
    ).all()
    delete_form = DeleteForm()
    return render_template('admin/entries.html', title=f'Obras para {contest.title}', entries=entries, contest=contest, delete_form=delete_form)

@bp.route('/contests/<int:contest_id>/entries/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_entry(contest_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    form = EntryForm()
    if form.validate_on_submit():
        f = form.image.data
        filename = None
        if f:
            filename = secure_filename(f.filename)
            try:
                f.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            except Exception as e:
                flash(f'Error al guardar la imagen: {e}', 'danger')
                return render_template('admin/entry_form.html', title='Añadir Obra', form=form, contest=contest)

        entry = Entry(
            title=form.title.data, 
            description=form.description.data, 
            image_filename=filename, 
            contest_id=contest.id
        )
        db.session.add(entry)
        db.session.commit()
        flash('Obra añadida exitosamente.', 'success')
        return redirect(url_for('admin.list_entries', contest_id=contest.id))
    return render_template('admin/entry_form.html', title='Añadir Obra', form=form, contest=contest)

@bp.route('/contests/<int:contest_id>/entries/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_entry(contest_id, entry_id):
    contest = db.session.get(Contest, contest_id)
    if not contest:
        abort(404)
    entry = db.session.get(Entry, entry_id)
    if not entry:
        abort(404)
    form = EntryForm(obj=entry)
    if form.validate_on_submit():
        entry.title = form.title.data
        entry.description = form.description.data
        f = form.image.data
        if f: # If a new image is uploaded
             # Optionally delete old image file here
            filename = secure_filename(f.filename)
            try:
                f.save(os.path.join(Config.UPLOAD_FOLDER, filename))
                entry.image_filename = filename # Update filename only if save succeeds
            except Exception as e:
                flash(f'Error al guardar la nueva imagen: {e}', 'danger')
                # Don't proceed with db commit if image save failed?
                return render_template('admin/entry_form.html', title='Editar Obra', form=form, contest=contest, entry=entry)
        
        db.session.commit()
        flash('Obra actualizada exitosamente.', 'success')
        return redirect(url_for('admin.list_entries', contest_id=contest.id))
    elif request.method == 'GET':
        form.image.data = None # Clear file input on GET

    return render_template('admin/entry_form.html', title='Editar Obra', form=form, contest=contest, entry=entry)

@bp.route('/contests/<int:contest_id>/entries/delete/<int:entry_id>', methods=['POST'])
@login_required
@admin_required
def delete_entry(contest_id, entry_id):
    form = DeleteForm()
    if form.validate_on_submit():
        entry = db.session.get(Entry, entry_id)
        if not entry:
            abort(404)
        # Add logic to delete image file from server if it exists
        if entry.image_filename:
            try:
                os.remove(os.path.join(Config.UPLOAD_FOLDER, entry.image_filename))
            except OSError as e:
                flash(f'Error al eliminar archivo de imagen: {e}', 'warning') # Warn but proceed

        # Delete related votes first to avoid integrity errors
        Vote.query.filter_by(entry_id=entry_id).delete()

        db.session.delete(entry)
        db.session.commit()
        flash('Obra eliminada exitosamente.', 'success')
    else:
         flash('Error al eliminar la obra.', 'danger')
    return redirect(url_for('admin.list_entries', contest_id=contest_id)) 