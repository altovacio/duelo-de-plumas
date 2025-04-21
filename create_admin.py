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

import os
import sys
from flask import Flask
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# Import after loading environment variables to ensure proper configuration
from app import create_app, db
from app.models import User

def create_admin_user():
    """Create an admin user using credentials from .env file"""
    # Get admin credentials from environment variables
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_email = os.getenv('ADMIN_EMAIL', '')  # Optional, empty string if not set
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    # Validate required credentials
    if not admin_username or not admin_password:
        print("Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env file")
        sys.exit(1)
    
    # Create and run app in application context
    app = create_app()
    with app.app_context():
        # Check if the admin user already exists
        existing_user = User.query.filter_by(username=admin_username).first()
        
        if existing_user:
            # If user exists, check if they have admin role
            if existing_user.role == 'admin':
                print(f"Admin user '{admin_username}' already exists.")
                update = input("Do you want to update this admin's password? (y/n): ").lower()
                
                if update == 'y':
                    # Update existing admin's password
                    existing_user.password_hash = generate_password_hash(admin_password)
                    db.session.commit()
                    print(f"Password updated for admin user '{admin_username}'")
                else:
                    print("No changes made.")
            else:
                # User exists but is not an admin
                print(f"User '{admin_username}' exists but is not an admin.")
                promote = input("Do you want to promote this user to admin? (y/n): ").lower()
                
                if promote == 'y':
                    # Promote user to admin
                    existing_user.role = 'admin'
                    existing_user.password_hash = generate_password_hash(admin_password)
                    db.session.commit()
                    print(f"User '{admin_username}' has been promoted to admin and password updated")
                else:
                    print("No changes made.")
        else:
            # Create new admin user
            admin = User(
                username=admin_username,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                role='admin',
                judge_type='human'
            )
            
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{admin_username}' created successfully")

if __name__ == "__main__":
    create_admin_user() 