from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Use standard form for login
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Relative imports from within v2
from ... import schemas, models
from ...database import get_db_session
from ... import security # Corrected: Go up two levels
from ...fastapi_config import settings # Corrected: Go up two levels

router = APIRouter()

@router.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), # Expects username/password form data
    db: AsyncSession = Depends(get_db_session)
):
    """Authenticates a user and returns a JWT access token."""
    # 1. Find the user by username
    user = await security.get_user_by_username(db, username=form_data.username)
    
    # 2. Check if user exists and password is correct
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Important for OAuth2
        )
        
    # 3. Create the access token
    access_token_expires = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.username, # Use username as subject (or user.id)
        expires_delta=access_token_expires
    )
    
    # 4. Return the token
    return {"access_token": access_token, "token_type": "bearer"}

# Optional: Endpoint to test authentication and get current user info
@router.get("/users/me", response_model=schemas.UserMe, tags=["Authentication"])
async def read_users_me(
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Returns the details of the currently authenticated user."""
    return current_user

# --- ADDED: User Registration Endpoint ---
@router.post(
    "/register", 
    response_model=schemas.UserPublic, 
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)
async def register_user(
    user_in: schemas.UserRegister, # Changed from UserCreate
    db: AsyncSession = Depends(get_db_session)
):
    """Registers a new user with the 'user' role.
    
    Checks for existing username/email and hashes the password.
    Role and judge_type are automatically set to 'user' and 'human'.
    """
    # Check for existing username
    existing_user = await security.get_user_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # --- ADDED: Check for existing email --- 
    stmt = select(models.User).where(models.User.email == user_in.email)
    existing_email_result = await db.execute(stmt)
    if existing_email_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # --- END ADDED --- 
        
    # Create user data dictionary from the specific input schema
    user_data = user_in.model_dump() # Dump all fields from UserRegister
    
    # Explicitly set role and judge_type for standard user registration
    user_data['role'] = 'user' 
    user_data['judge_type'] = 'human'
    
    # Prepare data for model (separate password for hashing)
    password_to_hash = user_data.pop('password') 
    new_user = models.User(**user_data) # Create model with username, email, role, judge_type
    
    # Set hashed password
    try:
        new_user.set_password(password_to_hash) # Use the separated password
    except Exception as e:
        # Catch potential errors during hashing (like the bcrypt issue)
        print(f"Error hashing password during registration: {e}") # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing registration."
        )

    # Add to DB
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback() # Rollback the session
        print(f"Database integrity error during registration: {e}") # Log the error
        # Determine if it was username or email - more robust check needed if both unique
        # For now, assume duplicate if checks passed earlier (shouldn't happen often)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already exists (Integrity Error)." # More generic message
        )
    except Exception as e:
        await db.rollback()
        print(f"Unknown database error during registration: {e}") # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred."
        )

    await db.refresh(new_user)
    
    return new_user
# --- END ADDED --- 