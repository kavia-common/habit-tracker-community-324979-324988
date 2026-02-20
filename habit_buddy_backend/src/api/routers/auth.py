from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.core.security import create_access_token, hash_password, verify_password
from src.api.deps import get_current_user
from src.api.models import User
from src.api.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
    UserUpdateRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description="Creates a new user and returns a JWT access token.",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a user account and return JWT token."""
    existing = db.execute(select(User).where(User.email == str(payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        timezone=payload.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Validates credentials and returns a JWT access token.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user = db.execute(select(User).where(User.email == str(payload.email))).scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
    description="Returns the current authenticated user's public profile.",
)
def me(current: User = Depends(get_current_user)) -> UserPublic:
    """Return current authenticated user."""
    return current


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update current user profile",
    description="Updates fields on the current user's profile.",
)
def update_me(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserPublic:
    """Update current user's profile."""
    if payload.display_name is not None:
        current.display_name = payload.display_name
    if payload.bio is not None:
        current.bio = payload.bio
    if payload.avatar_url is not None:
        current.avatar_url = payload.avatar_url
    if payload.timezone is not None:
        current.timezone = payload.timezone

    db.add(current)
    db.commit()
    db.refresh(current)
    return current
