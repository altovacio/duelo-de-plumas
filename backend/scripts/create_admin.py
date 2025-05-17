import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal, Base, engine
from app.db.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings
from dotenv import load_dotenv
from app.db.repositories.user_repository import UserRepository

# Import all models to ensure they're registered with Base.metadata
from app.db.models.text import Text
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.vote import Vote
from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.db.models.credit_transaction import CreditTransaction

# Load .env file
load_dotenv()

async def create_tables():
    """Create all database tables."""
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Tables in metadata: {Base.metadata.tables.keys()}")
    
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Creating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully")

async def create_admin_user(db: AsyncSession, username: str, email: str, password: str):
    """Create an admin user using the provided session."""
    # Check if user exists
    user_repo = UserRepository(db)
    
    existing_user = await user_repo.get_by_username(username)
    if existing_user:
        print(f"User with username '{username}' already exists.")
        return
        
    existing_user = await user_repo.get_by_email(email)
    if existing_user:
        print(f"User with email '{email}' already exists.")
        return
    
    # Create admin user
    hashed_password = get_password_hash(password)
    admin_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=True,
        credits=1000  # Give admin some initial credits
    )
    
    db.add(admin_user)
    await db.commit()
    # await db.refresh(admin_user) # Optional: if you need the ID or defaults back immediately
    
    print(f"Admin user '{username}' created successfully!")

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
    import inspect
    
    # If script called directly with arguments, handle admin creation
    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        # Try to get credentials from .env file if not provided as arguments
        if len(sys.argv) == 2:
            username = os.getenv("ADMIN_USERNAME")
            email = os.getenv("ADMIN_EMAIL")
            password = os.getenv("ADMIN_PASSWORD")
            
            if not all([username, email, password]):
                print("Admin credentials not found in .env file.")
                print("Please provide credentials as arguments or set them in .env file:")
                print("Usage: python create_admin.py admin <username> <email> <password>")
                print("Or add ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to .env file")
                sys.exit(1)
        elif len(sys.argv) != 5:
            print("Usage: python create_admin.py admin <username> <email> <password>")
            print("Or add ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to .env file")
            sys.exit(1)
        else:
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
        
        # Create admin user
        async def main_create_admin():
            async with AsyncSessionLocal() as session:
                await create_admin_user(session, username, email, password)
                
        print(f"Creating admin user: {username} ({email})")
        asyncio.run(main_create_admin())
    
    # If script called with 'tables' argument or no arguments, create tables
    elif len(sys.argv) <= 1 or sys.argv[1] == "tables":
        asyncio.run(create_tables())
    
    # If script called with 'setup' argument, run full database setup
    elif sys.argv[1] == "setup":
        asyncio.run(setup_database())
    
    # Display usage instructions
    else:
        print("Usage:")
        print("  python create_admin.py tables         - Create database tables")
        print("  python create_admin.py admin <username> <email> <password> - Create admin user")
        print("  python create_admin.py setup          - Create tables and default admin user")
        print("  python create_admin.py                - Show this help message") 