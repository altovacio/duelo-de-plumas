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
from dotenv import load_dotenv

# Load .env file
load_dotenv()

async def create_admin_user(username: str, email: str, password: str):
    """Create an admin user."""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        from app.services.auth_service import get_user_by_username, get_user_by_email
        
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            print(f"User with username '{username}' already exists.")
            return
            
        existing_user = await get_user_by_email(db, email)
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
        
        print(f"Admin user '{username}' created successfully!")

if __name__ == "__main__":
    # Try to get credentials from .env file if not provided as arguments
    if len(sys.argv) == 1:
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        
        if not all([username, email, password]):
            print("Admin credentials not found in .env file.")
            print("Please provide credentials as arguments or set them in .env file:")
            print("Usage: python create_admin.py <username> <email> <password>")
            print("Or add ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to .env file")
            sys.exit(1)
    elif len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        print("Or add ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to .env file")
        sys.exit(1)
    else:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
    
    print(f"Creating admin user: {username} ({email})")
    asyncio.run(create_admin_user(username, email, password)) 