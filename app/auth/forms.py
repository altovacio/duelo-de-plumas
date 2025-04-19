from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from app import db
from app.models import User

class LoginForm(FlaskForm):
    username_or_email = StringField('Nombre de Usuario o Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

# Removed RegistrationForm class again 