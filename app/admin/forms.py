import json
import os
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email, EqualTo, ValidationError
from app.models import User, UserRole, JudgeType

# Helper function to load available AI models for choices
def get_available_ai_models():
    choices = []
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_model_costs.json')
        with open(config_path, 'r') as f:
            all_models = json.load(f)
        available_models = [m for m in all_models if m.get('available', True)] # Default to True if missing?
        choices = [(m['id'], f"{m['name']} ({m['provider']})") for m in available_models]
    except Exception as e:
        print(f"Error loading AI model choices: {e}") # Use logging in real app
    # Add a default empty choice
    return [(None, '-- Selecciona un Modelo AI --')] + choices

class ContestForm(FlaskForm):
    title = StringField('Título del Concurso', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Descripción')
    # Use DateTimeLocalField for better browser support with datetime-local input type
    end_date = DateTimeField('Fecha Límite', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    required_judges = IntegerField('Número de Jueces Requerido', default=1, validators=[DataRequired(), NumberRange(min=1)])
    contest_type = SelectField('Tipo', choices=[('public', 'Público'), ('private', 'Privado')], validators=[DataRequired()])
    # Password only required if type is private (add custom validation logic in route or here)
    contest_password = PasswordField('Contraseña (si es Privado)', validators=[Optional()])
    anonymous_submissions = BooleanField('Permitir Envíos Anónimos (ocultar hasta cierre)')
    status = SelectField('Estado', choices=[('open', 'Abierto'), ('evaluation', 'En Evaluación'), ('closed', 'Cerrado')], validators=[DataRequired()], default='open')
    # Field to select judges (populate choices in the route)
    judges = SelectMultipleField('Jueces Asignados', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar Concurso')

    # Need to populate judge choices dynamically in the route
    def __init__(self, *args, **kwargs):
        super(ContestForm, self).__init__(*args, **kwargs)
        # Query users with the 'judge' role ONLY, using the Enum member
        judge_users = User.query.filter(
            User.role == UserRole.JUDGE # Use Enum Member for comparison
        ).order_by('username').all()
        # Use .value for judge_type enum in label, handle None case
        self.judges.choices = [(u.id, f"{u.username} ({u.judge_type.value if u.judge_type else 'N/A'})") for u in judge_users]

# Form for Admin to add or edit a Judge/User
# Renamed to UserForm for broader use (add/edit)
class UserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    # Password optional for editing, required for adding
    password = PasswordField('Contraseña', validators=[Optional()])
    password2 = PasswordField('Repetir Contraseña', validators=[Optional(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    # Remove hardcoded choices, they are set dynamically in the route
    role = SelectField('Rol', validators=[DataRequired()])
    
    # --- Judge Fields (conditionally shown) ---
    # Remove hardcoded choices/default, set dynamically. Make Optional, validation done in route/custom validate.
    judge_type = SelectField('Tipo de Juez', validators=[Optional()])
    # Populate AI model choices dynamically in __init__
    ai_model_id = SelectField('Modelo IA', choices=[], coerce=str, validators=[Optional()]) 
    ai_personality_prompt = TextAreaField('Prompt de Personalidad IA', validators=[Optional()])
    
    submit = SubmitField('Guardar Usuario')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        # Populate AI model choices
        self.ai_model_id.choices = get_available_ai_models()

    # Validation methods (ensure uniqueness, handle edits)
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este nombre de usuario ya está en uso. Por favor elige otro.')

    def validate_email(self, email):
         if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Esta dirección de email ya está registrada. Por favor usa otra.')
                
    # Custom validation: check conditional requirements based on raw form data
    def validate(self, **kwargs):
        # Run standard validators first
        if not super().validate(**kwargs):
            return False
        
        # If adding a user (no original username), password is required
        if not self.original_username and not self.password.data:
             self.password.errors.append('La contraseña es obligatoria para nuevos usuarios.')
             return False
    
        # Get raw string values
        role_value = self.role.data # e.g., 'user', 'judge', 'admin'
        judge_type_value = self.judge_type.data # e.g., 'human', 'ai', or None
    
        # If role is 'judge' (string comparison), judge_type is now required
        if role_value == UserRole.JUDGE.value: # Compare against Enum *value*
            if not judge_type_value:
                self.judge_type.errors.append('Debe seleccionar un tipo de Juez (Humano/IA) si el rol es Juez.')
                return False
            
            # If type is 'ai' (string comparison), require model
            if judge_type_value == JudgeType.AI.value: # Compare against Enum *value*
                # Check against None or the placeholder value if it exists
                # Assuming placeholder value is None based on get_available_ai_models() returning (None, '...')
                if not self.ai_model_id.data or self.ai_model_id.data == 'None': 
                    self.ai_model_id.errors.append('Se debe seleccionar un modelo de IA para un juez de tipo IA.')
                    return False
                # Prompt is optional
        
        # If role is not 'judge', ensure judge_type and AI fields are not mandatory validated here
        # (Route handler will nullify them anyway)
    
        return True

# Form for generic delete confirmation
class DeleteForm(FlaskForm):
    submit = SubmitField('Eliminar')

# --- New EntryForm ---
from flask_wtf.file import FileField, FileAllowed, FileRequired

class EntryForm(FlaskForm):
    title = StringField('Título de la Obra', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Descripción/Sinopsis', validators=[Optional()])
    # Use FileField for image upload
    image = FileField('Imagen (Opcional)', validators=[
        Optional(), # Image is optional
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '¡Solo se permiten imágenes!')
    ])
    submit = SubmitField('Guardar Obra')

# Ensure this form is imported where needed, e.g., in admin routes. 