from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Habit, HabitCheckin, HabitStreak, User
from src.api.schemas import (
    HabitCheckinCreateRequest,
    HabitCheckinResponse,
    HabitCreateRequest,
    HabitResponse,
    HabitStreakResponse,
    HabitUpdateRequest,
)

router = APIRouter(prefix="/habits", tags=["habits"])


def _get_user_habit(db: Session, user_id, habit_id) -> Habit:
    habit = db.execute(select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)).scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


def _recompute_streak(db: Session, habit: Habit) -> HabitStreak:
    """Recompute streak based on check-in dates (simple consecutive-day logic)."""
    checkins = (
        db.execute(
            select(HabitCheckin.checkin_date)
            .where(HabitCheckin.habit_id == habit.id)
            .order_by(desc(HabitCheckin.checkin_date))
            .limit(400)
        )
        .scalars()
        .all()
    )
    if not checkins:
        streak = db.get(HabitStreak, habit.id) or HabitStreak(habit_id=habit.id, current_streak=0, longest_streak=0)
        streak.current_streak = 0
        streak.last_checkin_date = None
        db.add(streak)
        db.commit()
        db.refresh(streak)
        return streak

    # consecutive days from latest backwards
    current = 1
    for i in range(1, len(checkins)):
        if checkins[i - 1] - checkins[i] == timedelta(days=1):
            current += 1
        else:
            break

    longest = max(current, db.get(HabitStreak, habit.id).longest_streak if db.get(HabitStreak, habit.id) else 0)

    streak = db.get(HabitStreak, habit.id) or HabitStreak(habit_id=habit.id, current_streak=0, longest_streak=0)
    streak.current_streak = current
    streak.longest_streak = max(streak.longest_streak, longest)
    streak.last_checkin_date = checkins[0]
    db.add(streak)
    db.commit()
    db.refresh(streak)
    return streak


@router.get(
    "",
    response_model=list[HabitResponse],
    summary="List habits",
    description="List all habits for the current user.",
)
def list_habits(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[HabitResponse]:
    """List all habits for current user."""
    return db.execute(select(Habit).where(Habit.user_id == current.id).order_by(desc(Habit.created_at))).scalars().all()


@router.post(
    "",
    response_model=HabitResponse,
    status_code=201,
    summary="Create habit",
    description="Create a new habit for the current user.",
)
def create_habit(
    payload: HabitCreateRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> HabitResponse:
    """Create a habit."""
    habit = Habit(user_id=current.id, **payload.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    # ensure streak row exists
    if not db.get(HabitStreak, habit.id):
        db.add(HabitStreak(habit_id=habit.id, current_streak=0, longest_streak=0))
        db.commit()
    return habit


@router.get(
    "/{habit_id}",
    response_model=HabitResponse,
    summary="Get habit",
    description="Get a single habit by id (owned by current user).",
)
def get_habit(habit_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> HabitResponse:
    """Get habit."""
    return _get_user_habit(db, current.id, habit_id)


@router.patch(
    "/{habit_id}",
    response_model=HabitResponse,
    summary="Update habit",
    description="Update a habit (owned by current user).",
)
def update_habit(
    habit_id,
    payload: HabitUpdateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> HabitResponse:
    """Update habit."""
    habit = _get_user_habit(db, current.id, habit_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(habit, k, v)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.delete(
    "/{habit_id}",
    status_code=204,
    summary="Delete habit",
    description="Delete a habit (owned by current user).",
)
def delete_habit(habit_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Delete habit."""
    habit = _get_user_habit(db, current.id, habit_id)
    db.delete(habit)
    db.commit()
    return None


@router.get(
    "/{habit_id}/streak",
    response_model=HabitStreakResponse,
    summary="Get habit streak",
    description="Returns the streak info for a habit.",
)
def get_streak(habit_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> HabitStreakResponse:
    """Get habit streak."""
    habit = _get_user_habit(db, current.id, habit_id)
    streak = db.get(HabitStreak, habit.id)
    if not streak:
        streak = HabitStreak(habit_id=habit.id, current_streak=0, longest_streak=0)
        db.add(streak)
        db.commit()
        db.refresh(streak)
    return streak


@router.post(
    "/{habit_id}/checkins",
    response_model=HabitCheckinResponse,
    status_code=201,
    summary="Create a check-in",
    description="Create a habit check-in for the given date. One check-in per habit per day.",
)
def create_checkin(
    habit_id,
    payload: HabitCheckinCreateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> HabitCheckinResponse:
    """Create a check-in and update streak."""
    habit = _get_user_habit(db, current.id, habit_id)

    checkin = HabitCheckin(
        habit_id=habit.id,
        user_id=current.id,
        checkin_date=payload.checkin_date,
        value=payload.value,
        note=payload.note,
    )
    db.add(checkin)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already checked in for this date")

    db.refresh(checkin)
    _recompute_streak(db, habit)
    return checkin


@router.get(
    "/{habit_id}/checkins",
    response_model=list[HabitCheckinResponse],
    summary="List check-ins",
    description="List check-ins for a habit (owned by current user).",
)
def list_checkins(
    habit_id,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    limit: int = 50,
) -> list[HabitCheckinResponse]:
    """List habit check-ins."""
    habit = _get_user_habit(db, current.id, habit_id)
    return (
        db.execute(
            select(HabitCheckin)
            .where(HabitCheckin.habit_id == habit.id)
            .order_by(desc(HabitCheckin.checkin_date))
            .limit(limit)
        )
        .scalars()
        .all()
    )
