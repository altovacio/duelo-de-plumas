import asyncio
import sys

# Import all models to get all tables defined
from app.db.models.user import User
from app.db.models.text import Text
from app.db.models.contest import Contest
from app.db.models.agent import Agent
from app.db.models.credit_transaction import CreditTransaction
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.agent_execution import AgentExecution
from app.db.models.vote import Vote

from app.db.database import Base, engine, AsyncSessionLocal
from app.core.config import settings
from scripts.create_tables import create_tables
from scripts.create_admin import create_admin_user

print(f"Database URL: {settings.DATABASE_URL}")

async def setup_database():
    """Set up the database by creating tables and admin user."""
    # Create tables
    await create_tables()
    
    # Create admin user
    async with AsyncSessionLocal() as session:
        username = settings.FIRST_SUPERUSER_USERNAME
        password = settings.FIRST_SUPERUSER_PASSWORD
        email = settings.FIRST_SUPERUSER_EMAIL
        await create_admin_user(session, username, email, password)

if __name__ == "__main__":
    asyncio.run(setup_database()) 