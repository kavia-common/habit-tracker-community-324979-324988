from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Notification, User
from src.api.schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse], summary="List notifications", description="List notifications.")
def list_notifications(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    limit: int = 50,
) -> list[NotificationResponse]:
    """List notifications for current user."""
    return (
        db.execute(
            select(Notification)
            .where(Notification.user_id == current.id)
            .order_by(desc(Notification.created_at))
            .limit(limit)
        )
        .scalars()
        .all()
    )


@router.post(
    "/{notification_id}/read",
    status_code=204,
    summary="Mark notification as read",
    description="Marks a single notification as read.",
)
def mark_read(notification_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Mark one notification read."""
    n = db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current.id)
    ).scalar_one_or_none()
    if not n:
        return None
    if not n.is_read:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        db.add(n)
        db.commit()
    return None


@router.post(
    "/read-all",
    status_code=204,
    summary="Mark all notifications as read",
    description="Marks all notifications as read for current user.",
)
def mark_all_read(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Mark all notifications read."""
    notifs = db.execute(select(Notification).where(Notification.user_id == current.id, Notification.is_read.is_(False))).scalars().all()
    if not notifs:
        return None
    now = datetime.now(timezone.utc)
    for n in notifs:
        n.is_read = True
        n.read_at = now
        db.add(n)
    db.commit()
    return None
