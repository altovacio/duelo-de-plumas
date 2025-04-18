from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models import User

class LoginForm(FlaskForm):
    username_or_email = StringField('Nombre de Usuario o Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

# Add other forms like registration if needed later
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    # Role will be set automatically for the first user
    submit = SubmitField('Registrar Cuenta')

    # Custom validators to check if username/email already exist
    def validate_username(self, username):
        user = db.session.scalar(db.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        user = db.session.scalar(db.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Esta dirección de email ya está registrada. Por favor, usa otra.') 