from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, Optional
from app.models import User, UserRole, JudgeType # Need User for validation

# Helper to get available roles for registration (exclude admin)
def get_registration_roles():
    # Exclude ADMIN from public registration choices
    return [(role.value, role.name.capitalize()) for role in UserRole if role != UserRole.ADMIN]

# --- Public Registration Form ---
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    
    # Role selection (User or Judge only)
    role = SelectField('Registrarse como', choices=get_registration_roles, validators=[DataRequired()])
    
    # Judge Type - Although forced to HUMAN in the route, include for consistency/future?
    # Or maybe hide/remove it completely from public registration form? Let's keep it hidden for now.
    # judge_type = SelectField('Tipo de Juez (si aplica)', choices=[(jtype.value, jtype.name.capitalize()) for jtype in JudgeType], default=JudgeType.HUMAN.value, validators=[Optional()])
    # AI fields - Not needed for public registration
    # ai_model_id = SelectField('Modelo IA (si aplica)', choices=[], coerce=str, validators=[Optional()])
    # ai_personality_prompt = TextAreaField('Prompt de Personalidad IA (si aplica)', validators=[Optional()])

    submit = SubmitField('Registrar')

    # Validation methods
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor elige otro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Esta dirección de email ya está registrada. Por favor usa otra.')

    # Add validation for role if needed (e.g., ensure it's not ADMIN)
    def validate_role(self, role):
        try:
            selected_role = UserRole(role.data)
            if selected_role == UserRole.ADMIN:
                 raise ValidationError('No se permite el registro como Administrador.')
        except ValueError:
             raise ValidationError('Rol inválido seleccionado.')


# --- User Profile Edit Form (Main) ---
class ProfileForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    # Password change is optional
    password = PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)', validators=[Optional()])
    password2 = PasswordField(
        'Repetir Nueva Contraseña', validators=[Optional(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Actualizar Perfil')

    # Store original values to check if they changed for validation
    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Esta dirección de email ya está registrada.') 