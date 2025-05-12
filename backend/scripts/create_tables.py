import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to ensure they're registered with Base.metadata
from app.db.models.user import User
from app.db.models.text import Text
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.vote import Vote
from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.db.models.credit_transaction import CreditTransaction

from app.db.database import Base, engine
from app.core.config import settings

print(f"Database URL: {settings.DATABASE_URL}")
print(f"Tables in metadata: {Base.metadata.tables.keys()}")

async def create_tables():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_tables()) 