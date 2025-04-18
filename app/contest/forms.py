from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, DateTimeField, SelectField, PasswordField, BooleanField, SelectMultipleField, FormField, FieldList, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models import User

class SubmissionForm(FlaskForm):
    author_name = StringField('Nombre del Autor', validators=[DataRequired(), Length(max=100)])
    title = StringField('Título del Texto', validators=[DataRequired(), Length(max=150)])
    text_content = TextAreaField('Contenido del Texto', validators=[DataRequired()])
    # Add validation for length or other constraints if needed in config.py
    submit = SubmitField('Enviar Texto')

# Represents a single row in the ranking form
class SubmissionRankForm(FlaskForm):
    submission_id = HiddenField() # Store submission ID
    # Places: 0=No Place, 1=1st, 2=2nd, 3=3rd, 4=HM
    place = SelectField('Lugar', coerce=int, choices=[(0, '---'), (1, '1º'), (2, '2º'), (3, '3º'), (4, 'M. Hon.')], default=0)
    comment = TextAreaField('Comentario (Opcional)') # Add comment field per submission
    # Add other fields per submission if needed

# Main form for ranking all submissions in a contest
class ContestEvaluationForm(FlaskForm):
    submissions = FieldList(FormField(SubmissionRankForm))
    # overall_comment = TextAreaField('Comentarios Generales (Opcional)') # Remove overall comment
    submit = SubmitField('Guardar Ranking y Comentarios')

    # Custom validation logic will be added here or in the route
    def validate_ranking(self, contest_submission_count):
        places_assigned = {1: 0, 2: 0, 3: 0, 4: 0} # Count assigned places
        assigned_submissions = set() # Track submissions assigned a place

        for submission_form in self.submissions:
            place = submission_form.place.data
            sub_id = submission_form.submission_id.data
            if place != 0: # 0 means no place assigned
                if place in places_assigned:
                    places_assigned[place] += 1
                    # Check for duplicate submission assignment
                    if sub_id in assigned_submissions:
                        raise ValidationError(f"La sumisión ID {sub_id} ha sido asignada a múltiples lugares.")
                    assigned_submissions.add(sub_id)
                else:
                    # This shouldn't happen with current choices, but good practice
                    raise ValidationError(f"Lugar inválido asignado: {place}")

        # Validate counts based on number of submissions
        if contest_submission_count < 3 and places_assigned[3] > 0:
            raise ValidationError("No se puede asignar 3er lugar con menos de 3 envíos.")
        if contest_submission_count < 2 and places_assigned[2] > 0:
            raise ValidationError("No se puede asignar 2do lugar con menos de 2 envíos.")
        if contest_submission_count < 1 and places_assigned[1] > 0:
            raise ValidationError("No se puede asignar 1er lugar con menos de 1 envío.")

        # Validate only one submission per place
        if places_assigned[1] > 1:
            raise ValidationError("Solo se puede asignar un 1er lugar.")
        if places_assigned[2] > 1:
            raise ValidationError("Solo se puede asignar un 2do lugar.")
        if places_assigned[3] > 1:
            raise ValidationError("Solo se puede asignar un 3er lugar.")
        # Allow multiple HMs (place 4)

        return True # Validation passed

class ContestForm(FlaskForm):
    # ... (existing ContestForm, including __init__) ...
    submit = SubmitField('Guardar Concurso')

    def __init__(self, *args, **kwargs):
        super(ContestForm, self).__init__(*args, **kwargs)
        self.judges.choices = [(u.id, u.username) for u in User.query.filter_by(role='judge').order_by('username').all()]
    # Add pass to fix indentation if no other methods are needed right now
    pass 