from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from app import db
from app.auth import bp
from app.auth.forms import LoginForm
from app.models import User

# Restore function to check if any users exist
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

# Removed the register() function again 