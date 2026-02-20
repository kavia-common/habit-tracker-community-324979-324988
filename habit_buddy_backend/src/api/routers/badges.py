from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Badge, User, UserBadge
from src.api.schemas import BadgeResponse, UserBadgeResponse

router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("", response_model=list[BadgeResponse], summary="List badges", description="List all badge definitions.")
def list_badges(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[BadgeResponse]:
    """List badge definitions."""
    return db.execute(select(Badge)).scalars().all()


@router.get(
    "/me",
    response_model=list[UserBadgeResponse],
    summary="List my earned badges",
    description="List badges earned by the current user.",
)
def list_my_badges(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[UserBadgeResponse]:
    """List user badges."""
    return db.execute(select(UserBadge).where(UserBadge.user_id == current.id)).scalars().all()
