from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

# Function to check if any users exist (Reinstated)
def check_no_users():
    return db.session.scalar(db.select(User).limit(1)) is None

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Redirect if already logged in
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = db.session.scalar(
            db.select(User).where(
                (User.username == form.username_or_email.data) | 
                (User.email == form.username_or_email.data)
            )
        )
        if user is None or not user.check_password(form.password.data):
            flash('Nombre de usuario, email o contraseña inválidos', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'¡Bienvenido de nuevo, {user.username}!', 'success')
        # Redirect to the page the user was trying to access, or to index
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index') 
        return redirect(next_page)
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@bp.route('/logout')
@login_required # User must be logged in to logout
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Ya has iniciado sesión.', 'info')
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    is_first_user = check_no_users() # Check if this will be the first user
    if form.validate_on_submit():
        # Determine role based on whether it's the first user
        user_role = 'admin' if is_first_user else 'judge'
        
        user = User(username=form.username.data, email=form.email.data, role=user_role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        if is_first_user:
            flash('¡Felicidades, eres el primer administrador registrado!', 'success')
            # Log the new admin in automatically
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('¡Felicidades, te has registrado exitosamente como juez! Por favor, inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
        
    # Adjust title based on whether it's the first registration
    title = 'Registrar Primer Admin' if is_first_user else 'Registrar Nueva Cuenta (Juez)'
    return render_template('auth/register.html', title=title, form=form, is_first_user=is_first_user)

# Add registration route later if needed 