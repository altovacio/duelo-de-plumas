# from app.services.auth_service import AuthService  # Commented out due to AuthService not being defined
from app.services.user_service import UserService
from app.services.text_service import TextService
from app.services.contest_service import ContestService
from app.services.vote_service import VoteService
from app.services.agent_service import AgentService
from app.services.ai_service import AIService
from app.services.credit_service import CreditService

# auth_service = AuthService() # Commented out
user_service = UserService()
text_service = TextService()
contest_service = ContestService()
vote_service = VoteService()
agent_service = AgentService()
ai_service = AIService()
credit_service = CreditService()

__all__ = [
    "user_service",
    "text_service",
    "contest_service",
    "vote_service",
    "agent_service",
    "ai_service",
    "credit_service",
    # "auth_service", # Commented out
] 