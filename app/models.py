from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager # Import db and login_manager from app.py

# Association table for Contest Judges (Many-to-Many)
contest_judges = db.Table('contest_judges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('contest_id', db.Integer, db.ForeignKey('contest.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(10), index=True, default='judge') # 'admin', 'judge', 'user' (submitter)
    # AI judge fields
    judge_type = db.Column(db.String(10), default='human') # 'human' or 'ai'
    ai_model = db.Column(db.String(50), nullable=True) # The AI model to use (e.g., 'gpt-4', 'claude-3-opus')
    ai_personality_prompt = db.Column(db.Text, nullable=True) # Prompt defining the AI judge's persona/evaluation focus
    votes = db.relationship('Vote', backref='judge', lazy='dynamic')
    # Relationship for contests a user is judging
    judged_contests = db.relationship('Contest', secondary=contest_judges,
                                      back_populates='judges', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_ai_judge(self):
        return self.role == 'judge' and self.judge_type == 'ai'

    def __repr__(self):
        if self.is_ai_judge():
            return f'<AI Judge {self.username} ({self.ai_model})>'
        return f'<User {self.username} ({self.role})>'

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id)) # Use db.session.get for Flask-SQLAlchemy >= 3.0

class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), index=True, default='open') # 'open', 'evaluation', 'closed'
    contest_type = db.Column(db.String(10), default='public') # 'public', 'private'
    password_hash = db.Column(db.String(256), nullable=True) # Only if contest_type is 'private'
    anonymous_submissions = db.Column(db.Boolean, default=False)
    required_judges = db.Column(db.Integer, default=1) # Number of judges needed to close evaluation
    submissions = db.relationship('Submission', backref='contest', lazy='dynamic', cascade="all, delete-orphan")
    # Relationship for judges assigned to this contest
    judges = db.relationship('User', secondary=contest_judges,
                             back_populates='judged_contests', lazy='dynamic')
    # Add relationship to AI evaluations
    ai_evaluations = db.relationship('AIEvaluation', backref='contest', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        if self.contest_type == 'private':
            self.password_hash = generate_password_hash(password)
        else:
            self.password_hash = None # Ensure public contests don't have passwords

    def check_password(self, password):
        if self.contest_type != 'private' or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Contest {self.title}>'

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100), nullable=False) # Assuming anonymous or non-logged-in submissions
    title = db.Column(db.String(150), nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)
    votes = db.relationship('Vote', backref='submission', lazy='dynamic', cascade="all, delete-orphan") # Cascade delete
    # Fields for final results
    total_points = db.Column(db.Integer, default=0)
    final_rank = db.Column(db.Integer, nullable=True) # 1, 2, 3, 4 (HM), etc.

    def __repr__(self):
        return f'<Submission {self.title} by {self.author_name}>'

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # score = db.Column(db.Integer, nullable=False) # Removed score
    place = db.Column(db.Integer, nullable=True) # 1, 2, 3, 4 (HM). Null if no place assigned by this judge.
    comment = db.Column(db.Text, nullable=True) # Overall comment for the contest by the judge? Or per-submission? Let's keep it per vote for now.
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)

    # A judge assigns places *per contest*. This constraint is now handled in the evaluation form logic.
    # We still need a constraint that a judge can only have one vote *per place* per contest, or simply one set of rankings per contest.
    # Let's rethink: Maybe Vote should store judge_id, contest_id, submission_id, place?
    # This seems better. A Vote record represents ONE judge assigning ONE place to ONE submission in ONE contest.
    # No, the original idea was one vote *per submission* per judge, storing the assigned place.
    # Let's stick with the current Vote structure (judge, submission, place, comment).
    # The logic that a judge only submits *one set* of rankings per contest is handled in the form processing.

    # Old unique constraint - needs updating or removal? Let's remove for now, form logic handles uniqueness.
    # __table_args__ = (db.UniqueConstraint('judge_id', 'submission_id', name='_judge_submission_uc'),)

    def __repr__(self):
        return f'<Vote by Judge {self.judge_id} on Submission {self.submission_id} -> Place: {self.place}>'

class AIEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ai_model = db.Column(db.String(50), nullable=False) # Record the specific model used
    full_prompt = db.Column(db.Text, nullable=False) # Store the complete prompt sent to the AI
    response_text = db.Column(db.Text, nullable=False) # Store the raw response from the AI
    prompt_tokens = db.Column(db.Integer, nullable=False) # Number of tokens in the prompt
    completion_tokens = db.Column(db.Integer, nullable=False) # Number of tokens in the response
    cost = db.Column(db.Float, nullable=False) # Cost in USD
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    judge = db.relationship('User', backref='ai_evaluations')
    
    def __repr__(self):
        return f'<AIEvaluation for Contest {self.contest_id} by Judge {self.judge_id}>' 