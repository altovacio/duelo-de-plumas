from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    
class UserCreate(UserBase):
    password: str
    
class UserResponse(UserBase):
    id: int
    is_admin: bool
    credits: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True
        
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
class UserCredit(BaseModel):
    amount: int
    description: str

class Token(BaseModel):
    access_token: str
    token_type: str
    is_first_login: Optional[bool] = False

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class UserAdminResponse(BaseModel):
    """User response for admin use - includes email"""
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True 