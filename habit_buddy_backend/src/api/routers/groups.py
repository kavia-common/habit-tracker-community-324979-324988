import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Group, GroupMember, User
from src.api.schemas import GroupCreateRequest, GroupResponse

router = APIRouter(prefix="/groups", tags=["groups"])


def _get_group(db: Session, group_id) -> Group:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.get("", response_model=list[GroupResponse], summary="List groups", description="List groups the user belongs to.")
def list_groups(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[GroupResponse]:
    """List groups for current user."""
    group_ids = db.execute(select(GroupMember.group_id).where(GroupMember.user_id == current.id)).scalars().all()
    if not group_ids:
        return []
    return db.execute(select(Group).where(Group.id.in_(group_ids))).scalars().all()


@router.post("", response_model=GroupResponse, status_code=201, summary="Create group", description="Create a group.")
def create_group(
    payload: GroupCreateRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> GroupResponse:
    """Create group and add owner as member."""
    invite_code = secrets.token_urlsafe(8)
    group = Group(
        name=payload.name,
        description=payload.description,
        owner_id=current.id,
        is_private=payload.is_private,
        invite_code=invite_code,
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    db.add(GroupMember(group_id=group.id, user_id=current.id, role="owner"))
    db.commit()
    return group


@router.get("/{group_id}", response_model=GroupResponse, summary="Get group", description="Get group by id.")
def get_group(group_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> GroupResponse:
    """Get group if member."""
    _ = db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == current.id)
    ).scalar_one_or_none()
    if not _:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    return _get_group(db, group_id)


@router.post(
    "/{group_id}/join",
    status_code=204,
    summary="Join group",
    description="Join a group by id (if not private or if you have invite code via separate flow).",
)
def join_group(group_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Join group by id."""
    group = _get_group(db, group_id)
    if group.is_private:
        # Minimal enforcement: private groups require invite code flow which isn't implemented yet
        raise HTTPException(status_code=403, detail="Group is private")

    exists = db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == current.id)
    ).scalar_one_or_none()
    if exists:
        return None

    db.add(GroupMember(group_id=group_id, user_id=current.id, role="member"))
    db.commit()
    return None


@router.post("/{group_id}/leave", status_code=204, summary="Leave group", description="Leave a group.")
def leave_group(group_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Leave group."""
    membership = db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == current.id)
    ).scalar_one_or_none()
    if not membership:
        return None
    db.delete(membership)
    db.commit()
    return None
