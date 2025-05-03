#!/usr/bin/env python
"""
Create Admin Script for Duelo de Plumas

This script creates an admin user using credentials from the .env file.
It can be used for initial setup or to update admin credentials.

Environment variables required in .env file:
- ADMIN_USERNAME
- ADMIN_EMAIL (optional)
- ADMIN_PASSWORD
"""

import asyncio
import os
import sys
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Ensure the script can find the backend package
# Assumes this script is run from the project root directory
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__)) # Add project root to path

# Now try importing from backend
try:
    from backend import models
    from backend.database import AsyncSessionFactory, Base
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Please ensure you are running this script from the project root directory")
    print(f"and the backend package structure is correct.")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

async def create_admin():
    """Creates the specified admin user directly in the database using .env variables."""
    # Get credentials from environment variables
    username = os.getenv("ADMIN_USERNAME")
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    # Validate required credentials
    if not username or not password:
        print("Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set in the .env file.")
        sys.exit(1)
    
    # Use a default if email is missing but not strictly required
    if not email:
        print("Warning: ADMIN_EMAIL not set in .env file. Using a placeholder.")
        email = f"{username}@placeholder.email" 

    async with AsyncSessionFactory() as session:
        async with session.begin(): # Use session.begin() for transaction management
            # Check if user already exists
            stmt = select(models.User).where(
                (models.User.username == username) | (models.User.email == email)
            )
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                if existing_user.role == 'admin':
                    print(f"Admin user '{username}' already exists.")
                    # Optionally add logic here to update password if desired
                    return 
                else:
                    print(f"User '{username}' or email '{email}' exists but is not admin. Promoting.")
                    existing_user.role = 'admin'
                    existing_user.judge_type = 'human' # Ensure judge_type is set
                    existing_user.set_password(password)
                    session.add(existing_user)
                    print(f"User '{username}' promoted to admin and password set.")
            else:
                # Create new admin user
                admin_user = models.User(
                    username=username,
                    email=email,
                    role='admin',
                    judge_type='human' # Default judge_type
                )
                admin_user.set_password(password) # Hash the password using the model method
                session.add(admin_user)
                print(f"Admin user '{username}' created successfully.")
            
            # Commit is handled by session.begin() context manager on successful exit
            # Rollback is handled on exception

async def main():
    # Optional: Initialize DB if tables don't exist (useful for first run)
    # This might require the engine too if you uncomment
    # from backend.database import async_engine 
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    await create_admin()

if __name__ == "__main__":
    print("Attempting to create admin user...")
    asyncio.run(main())
    print("Script finished.") 