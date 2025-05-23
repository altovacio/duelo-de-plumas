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
    
    class Config:
        from_attributes = True
        
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
class UserCredit(BaseModel):
    credits: int

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None 