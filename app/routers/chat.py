# app/routers/chat.py

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import User, Conversation, Message, UserProfile
from ..schemas.chat import (
    MessageCreate,
    MessageRead,
    ConversationCreate,
    ConversationRead,
    ConversationDetail,
    ChatResponse,
    UserProfileRead,
    UserProfileUpdate,
)
from ..auth import get_current_user
from ..config import settings

# Claude API client
try:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
except ImportError:
    claude_client = None

router = APIRouter(prefix="/chat", tags=["Chat"])


def build_system_prompt(user: User, profile: Optional[UserProfile]) -> str:
    """Build system prompt with user context"""
    base_prompt = """You are a helpful assistant for Frederick Fire and Safety. 
You help customers inquire about fire extinguishers and safety equipment.
You remember previous conversations and user preferences.
Be friendly, helpful, and professional."""
    
    if profile:
        context_parts = []
        if profile.display_name:
            context_parts.append(f"Customer name: {profile.display_name}")
        if profile.company_name:
            context_parts.append(f"Company: {profile.company_name}")
        if profile.phone:
            context_parts.append(f"Phone: {profile.phone}")
        if profile.preferences:
            context_parts.append(f"Preferences: {profile.preferences}")
        if profile.notes:
            context_parts.append(f"Notes: {profile.notes}")
        
        if context_parts:
            context = "\n".join(context_parts)
            base_prompt += f"\n\nKnown information about this customer:\n{context}"
    
    return base_prompt


def get_conversation_history(session: Session, conversation_id: int, limit: int = None) -> List[dict]:
    """Get message history for Claude API format"""
    limit = limit or settings.MAX_CONVERSATION_HISTORY
    
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = session.exec(statement).all()
    
    # Reverse to chronological order and format for Claude
    return [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(messages)
    ]


def call_claude(system_prompt: str, messages: List[dict], new_message: str) -> str:
    """Call Claude API and return response"""
    if not claude_client:
        # Fallback for testing without API key
        return f"[Demo mode - Claude API not configured] I received your message: '{new_message}'. To enable real responses, set your ANTHROPIC_API_KEY."
    
    # Add the new user message to history
    full_messages = messages + [{"role": "user", "content": new_message}]
    
    try:
        response = claude_client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=full_messages
        )
        return response.content[0].text
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."


# --- Conversation Endpoints ---

@router.get("/conversations", response_model=List[ConversationRead])
def list_conversations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all conversations for the current user"""
    statement = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = session.exec(statement).all()
    return conversations


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: ConversationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=current_user.id,
        title=conv_in.title or "New Conversation",
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a conversation with all messages"""
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conversation = session.exec(statement).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    msg_statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = session.exec(msg_statement).all()
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageRead.model_validate(m) for m in messages]
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation and all its messages"""
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conversation = session.exec(statement).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Delete messages first
    msg_statement = select(Message).where(Message.conversation_id == conversation_id)
    messages = session.exec(msg_statement).all()
    for msg in messages:
        session.delete(msg)
    
    session.delete(conversation)
    session.commit()


# --- Chat Endpoint ---

@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
def send_message(
    conversation_id: int,
    message_in: MessageCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get a response from the chatbot"""
    # Verify conversation belongs to user
    conv_statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conversation = session.exec(conv_statement).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get user profile for context
    profile_statement = select(UserProfile).where(UserProfile.user_id == current_user.id)
    profile = session.exec(profile_statement).first()
    
    # Build system prompt with user context
    system_prompt = build_system_prompt(current_user, profile)
    
    # Get conversation history
    history = get_conversation_history(session, conversation_id)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_in.content
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)
    
    # Get response from Claude
    assistant_response = call_claude(system_prompt, history, message_in.content)
    
    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_response
    )
    session.add(assistant_message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    
    session.commit()
    session.refresh(assistant_message)
    
    return ChatResponse(
        conversation_id=conversation_id,
        user_message=MessageRead.model_validate(user_message),
        assistant_message=MessageRead.model_validate(assistant_message)
    )


# --- Quick Chat Endpoint (creates conversation if needed) ---

@router.post("/message", response_model=ChatResponse)
def quick_message(
    message_in: MessageCreate,
    conversation_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Send a message, optionally creating a new conversation"""
    if conversation_id:
        # Use existing conversation
        conv_statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        conversation = session.exec(conv_statement).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        # Use first few words of message as title
        title = message_in.content[:50] + "..." if len(message_in.content) > 50 else message_in.content
        conversation = Conversation(
            user_id=current_user.id,
            title=title
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    
    # Now send the message using the conversation
    return send_message(conversation.id, message_in, session, current_user)


# --- User Profile Endpoints ---

@router.get("/profile", response_model=UserProfileRead)
def get_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get current user's profile"""
    statement = select(UserProfile).where(UserProfile.user_id == current_user.id)
    profile = session.exec(statement).first()
    
    if not profile:
        # Create profile if doesn't exist
        profile = UserProfile(user_id=current_user.id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    
    return profile


@router.patch("/profile", response_model=UserProfileRead)
def update_profile(
    profile_in: UserProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile"""
    statement = select(UserProfile).where(UserProfile.user_id == current_user.id)
    profile = session.exec(statement).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
    
    # Update only provided fields
    update_data = profile_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return profile
