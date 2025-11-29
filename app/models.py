# app/models.py

from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Text


class User(SQLModel, table=True):
    """User model - email is the sole identifier"""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String(255), unique=True, index=True, nullable=False))
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="user")
    profile: Optional["UserProfile"] = Relationship(back_populates="user")


class UserProfile(SQLModel, table=True):
    """Stores learned information about the user for context injection"""
    __tablename__ = "user_profile"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    
    # Basic info the bot learns
    display_name: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    company_name: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    phone: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    
    # Preferences and notes (JSON-like text for flexibility)
    preferences: Optional[str] = Field(default=None, sa_column=Column(Text))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    user: Optional[User] = Relationship(back_populates="profile")


class Conversation(SQLModel, table=True):
    """A conversation thread belonging to a user"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """A single message in a conversation"""
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    
    role: str = Field(sa_column=Column(String(20)))  # "user" or "assistant"
    content: str = Field(sa_column=Column(Text))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
