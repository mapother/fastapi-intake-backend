# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    """Registration request - email only"""
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """User response - public info"""
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
