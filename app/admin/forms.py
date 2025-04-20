from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email, EqualTo, ValidationError
from app.models import User
from app.config.ai_judge_params import AI_MODELS
from flask import request

# Form for associating a judge with a contest and specifying an AI model if applicable
class JudgeWithModelForm(FlaskForm):
    judge_id = SelectField('Juez', coerce=int, validators=[DataRequired()])
    ai_model = SelectField('Modelo de IA', validators=[Optional()], default='')

class ContestForm(FlaskForm):
    title = StringField('Título del Concurso', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Descripción')
    # Use DateTimeLocalField for better browser support with datetime-local input type
    end_date = DateTimeField('Fecha Límite', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    required_judges = IntegerField('Número de Jueces Requerido', default=1, validators=[DataRequired(), NumberRange(min=1)])
    contest_type = SelectField('Tipo', choices=[('public', 'Público'), ('private', 'Privado')], validators=[DataRequired()])
    # Password only required if type is private (add custom validation logic in route or here)
    contest_password = PasswordField('Contraseña (si es Privado)', validators=[Optional()])
    status = SelectField('Estado', choices=[('open', 'Abierto'), ('evaluation', 'En Evaluación'), ('closed', 'Cerrado')], validators=[DataRequired()], default='open')
    # Field to select judges (populate choices in the route)
    judges = SelectMultipleField('Jueces Asignados', coerce=int, validators=[Optional()])
    # Dictionary to store judge_id -> ai_model selections (will be populated in the route handler)
    judge_models = {}
    submit = SubmitField('Guardar Concurso')

    # Need to populate judge choices dynamically in the route
    def __init__(self, *args, **kwargs):
        super(ContestForm, self).__init__(*args, **kwargs)
        
        # Initialize judges.data to an empty list if not provided
        if not hasattr(self.judges, 'data') or self.judges.data is None:
            self.judges.data = []
            
        # Create choices - no need for headers now that we're using checkboxes
        self.judges.choices = []
        
        # Get the judges from the database
        try:
            human_judges = User.query.filter_by(role='judge', judge_type='human').order_by('username').all()
            ai_judges = User.query.filter_by(role='judge', judge_type='ai').order_by('username').all()
            
            # Add human judges with name only
            for judge in human_judges:
                self.judges.choices.append((judge.id, f"{judge.username}"))
            
            # Add AI judges with personality only
            for judge in ai_judges:
                self.judges.choices.append((judge.id, f"{judge.username}"))
                
            # Initialize the dictionary for judge_id -> ai_model
            self.judge_models = {judge.id: '' for judge in ai_judges}
        except Exception as e:
            # If there's an error querying the database, log it and provide empty choices
            print(f"Error loading judges: {e}")
            self.judges.choices = []
                
        # Process the form data in the route, not here (to avoid conflicts)

# Form for resetting a private contest's password
class ResetContestPasswordForm(FlaskForm):
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('new_password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Cambiar Contraseña')

# Form for Admin to add a new Judge
class AddJudgeForm(FlaskForm):
    username = StringField('Nombre de Usuario del Juez', validators=[DataRequired(), Length(min=3, max=64)])
    # Optional: Add email if desired
    email = StringField('Email (Opcional)', validators=[Optional(), Email(), Length(max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Crear Juez')

    # Validation methods (ensure uniqueness)
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        if email.data: # Only validate if email is provided
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Esta dirección de email ya está registrada.')

# Form for Admin to add a new AI Judge
class AddAIJudgeForm(FlaskForm):
    username = StringField('Nombre del Juez IA', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email (Placeholder)', default='ai@duelo-de-plumas.com', validators=[Email(), Length(max=120)])
    ai_personality_prompt = TextAreaField('Personalidad del Juez', validators=[DataRequired()], 
                              description="Define la personalidad y el enfoque de evaluación de este juez. Este texto se combinará con las instrucciones básicas.")
    submit = SubmitField('Crear Juez IA')

    # Validation methods (ensure uniqueness)
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Este nombre de usuario ya está en uso.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Esta dirección de email ya está registrada.')

# Form for editing an AI Judge
class EditAIJudgeForm(FlaskForm):
    ai_personality_prompt = TextAreaField('Personalidad del Juez', validators=[DataRequired()],
                              description="Define la personalidad y el enfoque de evaluación de este juez. Este texto se combinará con las instrucciones básicas.")
    submit = SubmitField('Actualizar Juez IA') 