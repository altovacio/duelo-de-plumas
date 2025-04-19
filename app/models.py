from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager # Import db and login_manager from app.py
import enum

# Association table for Contest Judges (Many-to-Many)
contest_judges = db.Table('contest_judges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('contest_id', db.Integer, db.ForeignKey('contest.id'), primary_key=True)
)

# --- Enums for Roles and Judge Types ---
class UserRole(enum.Enum):
    USER = 'user'
    JUDGE = 'judge'
    ADMIN = 'admin'

class JudgeType(enum.Enum):
    HUMAN = 'human'
    AI = 'ai'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    # Use Enum for role, force VARCHAR storage
    role = db.Column(db.Enum(UserRole, native_enum=False), index=True, default=UserRole.JUDGE, nullable=False)
    # Use Enum for judge_type, force VARCHAR storage (consistency)
    judge_type = db.Column(db.Enum(JudgeType, native_enum=False), nullable=True) # Nullable for non-judges
    ai_model_id = db.Column(db.String(80), nullable=True) # ID referencing ai_model_costs.json
    ai_personality_prompt = db.Column(db.Text, nullable=True) # Custom prompt for this AI judge

    votes = db.relationship('Vote', backref='judge', lazy='dynamic')
    # Relationship for contests a user is judging
    judged_contests = db.relationship('Contest', secondary=contest_judges,
                                      back_populates='judges', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_ai_judge(self):
        return self.judge_type == JudgeType.AI

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'

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
    # Relationship to AI evaluation runs for this contest
    # ai_evaluation_runs backref defined in AIEvaluationRun

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
    place = db.Column(db.Integer, nullable=True) # 1, 2, 3, 4 (HM).
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)

    # Relationships (optional but good practice)
    # submission = db.relationship('Submission', backref=db.backref('all_votes', lazy='dynamic')) # Renamed backref
    # judge = db.relationship('User', backref=db.backref('all_votes', lazy='dynamic')) # Renamed backref
    # contest = db.relationship('Contest', backref=db.backref('all_votes', lazy='dynamic')) # Renamed backref

    # Unique constraint: one vote (place/comment) per judge per submission
    __table_args__ = (db.UniqueConstraint('judge_id', 'submission_id', name='_judge_submission_uc'),)

    def __repr__(self):
        return f'<Vote Judge:{self.judge_id} Sub:{self.submission_id} Contest:{self.contest_id} -> Place:{self.place}>'

# New Model for AI Evaluation Runs
class AIEvaluationRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # The AI User running this
    ai_model_used = db.Column(db.String(80), nullable=False) # ID of the model used
    prompt_tokens = db.Column(db.Integer, nullable=True) # Input tokens for the run
    completion_tokens = db.Column(db.Integer, nullable=True) # Output tokens for the run
    total_cost = db.Column(db.Float, nullable=True) # Calculated cost for the run
    full_prompt_sent = db.Column(db.Text, nullable=True) # For debugging/auditing
    raw_ai_response = db.Column(db.Text, nullable=True) # For debugging/auditing
    run_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # Use timezone-aware UTC
    status = db.Column(db.String(20), default='pending', nullable=False) # 'pending', 'running', 'completed', 'failed'

    # Relationships
    contest = db.relationship('Contest', backref=db.backref('ai_evaluation_runs', lazy='dynamic'))
    judge = db.relationship('User', backref=db.backref('ai_evaluation_runs', lazy='dynamic'))

    # Ensure one AI judge only runs evaluation once per contest (can be relaxed later if needed)
    __table_args__ = (db.UniqueConstraint('contest_id', 'judge_id', name='_ai_run_contest_judge_uc'),)

    def __repr__(self):
        return f'<AIEvaluationRun {self.id} for Contest {self.contest_id} by Judge {self.judge_id} ({self.status})>'

# --- Entry Model ---
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(120), nullable=True) # Path relative to UPLOAD_FOLDER
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)
    
    # Removed the relationship to votes as Vote model doesn't link back to Entry
    # votes = db.relationship('Vote', backref='entry', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Entry {self.title}>' 