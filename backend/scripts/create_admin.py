import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings
from app.db.repositories.user_repository import UserRepository

async def create_admin_user(db: AsyncSession, username: str, email: str, password: str):
    """Create an admin user using the provided session."""
    # Check if user exists
    user_repo = UserRepository(db)
    
    try:
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            print(f"User with username '{username}' already exists.")
            return
            
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            print(f"User with email '{email}' already exists.")
            return
    except Exception as e:
        print(f"Error checking existing users: {e}")
        print("This might be because tables don't exist yet. Skipping admin user creation.")
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
    
    print(f"Admin user '{username}' created successfully!")

async def main():
    """Main function to create admin user."""
    # Get credentials from settings
    username = settings.FIRST_SUPERUSER_USERNAME
    email = settings.FIRST_SUPERUSER_EMAIL
    password = settings.FIRST_SUPERUSER_PASSWORD
    
    if not all([username, email, password]):
        print("Admin credentials not found in settings.")
        print("Please set FIRST_SUPERUSER_USERNAME, FIRST_SUPERUSER_EMAIL, and FIRST_SUPERUSER_PASSWORD in .env file")
        return
    
    print(f"Creating admin user: {username} ({email})")
    
    async with AsyncSessionLocal() as session:
        await create_admin_user(session, username, email, password)

if __name__ == "__main__":
    asyncio.run(main()) 