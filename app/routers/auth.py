# app/routers/auth.py

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import User, UserProfile
from ..schemas.user import UserCreate, UserRead
from ..schemas.auth import LoginRequest, Token
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
):
    """Register a new user with email and password"""
    # Check email uniqueness
    statement = select(User).where(User.email == user_in.email)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    # Create user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Create empty profile for user
    profile = UserProfile(user_id=user.id)
    session.add(profile)
    session.commit()

    return user


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session),
):
    """Login with email and password, returns JWT token"""
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current logged-in user info"""
    return current_user
