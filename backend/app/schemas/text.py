from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TextBase(BaseModel):
    title: str
    content: str  # Markdown content
    author: str  # This can be different from the owner


class TextCreate(TextBase):
    pass


class TextUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None


class TextResponse(TextBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 