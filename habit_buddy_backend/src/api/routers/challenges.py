from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Challenge, ChallengeParticipant, GroupMember, User
from src.api.schemas import ChallengeCreateRequest, ChallengeResponse

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("", response_model=list[ChallengeResponse], summary="List challenges", description="List challenges.")
def list_challenges(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[ChallengeResponse]:
    """List challenges: those created by user or in groups they belong to."""
    group_ids = db.execute(select(GroupMember.group_id).where(GroupMember.user_id == current.id)).scalars().all()

    stmt = select(Challenge).order_by(desc(Challenge.created_at))
    if group_ids:
        stmt = stmt.where((Challenge.creator_id == current.id) | (Challenge.group_id.in_(group_ids)))
    else:
        stmt = stmt.where(Challenge.creator_id == current.id)

    return db.execute(stmt).scalars().all()


@router.post("", response_model=ChallengeResponse, status_code=201, summary="Create challenge", description="Create a challenge.")
def create_challenge(
    payload: ChallengeCreateRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> ChallengeResponse:
    """Create a challenge."""
    if payload.group_id is not None:
        is_member = db.execute(
            select(GroupMember).where(GroupMember.group_id == payload.group_id, GroupMember.user_id == current.id)
        ).scalar_one_or_none()
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a member of the group")

    ch = Challenge(creator_id=current.id, **payload.model_dump())
    db.add(ch)
    db.commit()
    db.refresh(ch)

    # auto-join creator
    db.add(ChallengeParticipant(challenge_id=ch.id, user_id=current.id))
    db.commit()

    return ch


@router.post(
    "/{challenge_id}/join",
    status_code=204,
    summary="Join challenge",
    description="Join a challenge as a participant.",
)
def join_challenge(
    challenge_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> None:
    """Join challenge."""
    ch = db.get(Challenge, challenge_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    exists = db.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id, ChallengeParticipant.user_id == current.id
        )
    ).scalar_one_or_none()
    if exists:
        return None

    db.add(ChallengeParticipant(challenge_id=challenge_id, user_id=current.id))
    db.commit()
    return None
