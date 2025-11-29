# app/schemas/auth.py

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request - email is the identifier"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
