# First import base models
from app.db.models.user import User
from app.db.models.text import Text
from app.db.models.contest import Contest
from app.db.models.agent import Agent

# Then import models with relationships to the base models
from app.db.models.credit_transaction import CreditTransaction
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.contest_member import ContestMember
from app.db.models.agent_execution import AgentExecution
from app.db.models.vote import Vote

# Import any remaining models
# This ensures the SQLAlchemy mapper properly initializes relationships 