# app/schemas/chat.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# --- Message Schemas ---

class MessageCreate(BaseModel):
    """Send a message to the chatbot"""
    content: str


class MessageRead(BaseModel):
    """A message in the conversation"""
    id: int
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    """Create a new conversation (optional title)"""
    title: Optional[str] = None


class ConversationRead(BaseModel):
    """Conversation summary"""
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationRead):
    """Conversation with messages"""
    messages: List[MessageRead] = []


# --- Chat Response ---

class ChatResponse(BaseModel):
    """Response from sending a message"""
    conversation_id: int
    user_message: MessageRead
    assistant_message: MessageRead


# --- User Profile Schemas ---

class UserProfileUpdate(BaseModel):
    """Update user profile (learned info)"""
    display_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None


class UserProfileRead(BaseModel):
    """User profile response"""
    id: int
    display_name: Optional[str]
    company_name: Optional[str]
    phone: Optional[str]
    preferences: Optional[str]
    notes: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True
