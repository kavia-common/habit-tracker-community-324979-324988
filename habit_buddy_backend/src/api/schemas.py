import uuid
from datetime import date, datetime, time
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    message: str = Field(..., description="Health check message")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (unique)")
    password: str = Field(..., min_length=6, description="User password")
    display_name: str = Field(..., min_length=1, description="Public display name")
    timezone: str | None = Field(None, description="IANA timezone name")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, description="New display name")
    bio: str | None = Field(None, description="Bio")
    avatar_url: str | None = Field(None, description="Avatar URL")
    timezone: str | None = Field(None, description="IANA timezone name")


class HabitCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Habit title")
    description: str | None = Field(None, description="Habit description")
    habit_type: str = Field("daily", description="Habit type (e.g., daily)")
    target_value: int | None = Field(None, ge=0, description="Target value")
    unit: str | None = Field(None, description="Target unit")
    schedule_days: list[int] | None = Field(None, description="Days of week 1-7")
    reminder_time: time | None = Field(None, description="Daily reminder time")
    is_public: bool = Field(False, description="Whether habit is public")
    color: str | None = Field(None, description="UI color")
    icon: str | None = Field(None, description="UI icon name")


class HabitUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1)
    description: str | None = None
    habit_type: str | None = None
    target_value: int | None = Field(None, ge=0)
    unit: str | None = None
    schedule_days: list[int] | None = None
    reminder_time: time | None = None
    is_public: bool | None = None
    color: str | None = None
    icon: str | None = None


class HabitResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    habit_type: str
    target_value: int | None
    unit: str | None
    schedule_days: list[int] | None
    reminder_time: time | None
    is_public: bool
    color: str | None
    icon: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HabitStreakResponse(BaseModel):
    habit_id: uuid.UUID
    current_streak: int
    longest_streak: int
    last_checkin_date: date | None

    class Config:
        from_attributes = True


class HabitCheckinCreateRequest(BaseModel):
    checkin_date: date = Field(..., description="Date of check-in")
    value: int | None = Field(None, ge=0, description="Optional numeric value")
    note: str | None = Field(None, description="Optional note")


class HabitCheckinResponse(BaseModel):
    id: uuid.UUID
    habit_id: uuid.UUID
    user_id: uuid.UUID
    checkin_date: date
    value: int | None
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Group name")
    description: str | None = Field(None, description="Group description")
    is_private: bool = Field(False, description="Private group flag")


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    is_private: bool
    invite_code: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChallengeCreateRequest(BaseModel):
    group_id: uuid.UUID | None = Field(None, description="Associated group id (optional)")
    title: str = Field(..., min_length=1, description="Challenge title")
    description: str | None = Field(None, description="Challenge description")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    goal_type: str = Field("streak", description="Goal type (streak/value)")
    goal_value: int | None = Field(None, ge=0, description="Goal numeric value")


class ChallengeResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID | None
    creator_id: uuid.UUID
    title: str
    description: str | None
    start_date: date
    end_date: date
    goal_type: str
    goal_value: int | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BadgeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    icon: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    user_id: uuid.UUID
    badge_id: uuid.UUID
    earned_at: datetime
    context: dict[str, Any] | None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    body: str | None
    data: dict[str, Any] | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None

    class Config:
        from_attributes = True


class FeedPostCreateRequest(BaseModel):
    group_id: uuid.UUID | None = Field(None, description="Optional group id")
    post_type: Literal["text", "achievement"] = Field("text", description="Post type")
    content: str | None = Field(None, description="Post content text")
    data: dict[str, Any] | None = Field(None, description="Optional structured data")


class FeedPostResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    group_id: uuid.UUID | None
    post_type: str
    content: str | None
    data: dict[str, Any] | None
    like_count: int
    comment_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeedCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Comment content")


class FeedCommentResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
