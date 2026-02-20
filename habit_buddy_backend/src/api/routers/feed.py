from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import FeedPost, FeedPostComment, FeedPostLike, GroupMember, User
from src.api.schemas import (
    FeedCommentCreateRequest,
    FeedCommentResponse,
    FeedPostCreateRequest,
    FeedPostResponse,
)

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get(
    "",
    response_model=list[FeedPostResponse],
    summary="List feed posts",
    description="List community feed posts. If group_id provided, filters to that group (requires membership).",
)
def list_feed(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    group_id=None,
    limit: int = 50,
) -> list[FeedPostResponse]:
    """List feed posts."""
    stmt = select(FeedPost).order_by(desc(FeedPost.created_at)).limit(limit)

    if group_id is not None:
        is_member = db.execute(
            select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == current.id)
        ).scalar_one_or_none()
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a member of the group")
        stmt = stmt.where(FeedPost.group_id == group_id)

    return db.execute(stmt).scalars().all()


@router.post(
    "",
    response_model=FeedPostResponse,
    status_code=201,
    summary="Create feed post",
    description="Create a feed post. If group_id is set, requires membership.",
)
def create_post(
    payload: FeedPostCreateRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)
) -> FeedPostResponse:
    """Create a feed post."""
    if payload.group_id is not None:
        is_member = db.execute(
            select(GroupMember).where(GroupMember.group_id == payload.group_id, GroupMember.user_id == current.id)
        ).scalar_one_or_none()
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a member of the group")

    post = FeedPost(user_id=current.id, **payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.post(
    "/{post_id}/comments",
    response_model=FeedCommentResponse,
    status_code=201,
    summary="Create comment",
    description="Add a comment to a post.",
)
def comment(
    post_id,
    payload: FeedCommentCreateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> FeedCommentResponse:
    """Create a comment and update comment_count."""
    post = db.get(FeedPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    c = FeedPostComment(post_id=post.id, user_id=current.id, content=payload.content)
    db.add(c)
    post.comment_count = int(post.comment_count or 0) + 1
    db.add(post)
    db.commit()
    db.refresh(c)
    return c


@router.post(
    "/{post_id}/like",
    status_code=204,
    summary="Like post",
    description="Like a post (idempotent).",
)
def like(post_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Like a post and increment like_count."""
    post = db.get(FeedPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like_row = FeedPostLike(post_id=post.id, user_id=current.id)
    db.add(like_row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None

    post.like_count = int(post.like_count or 0) + 1
    db.add(post)
    db.commit()
    return None


@router.post(
    "/{post_id}/unlike",
    status_code=204,
    summary="Unlike post",
    description="Remove like (idempotent).",
)
def unlike(post_id, db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> None:
    """Unlike a post and decrement like_count."""
    post = db.get(FeedPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like_row = db.execute(
        select(FeedPostLike).where(FeedPostLike.post_id == post.id, FeedPostLike.user_id == current.id)
    ).scalar_one_or_none()
    if not like_row:
        return None

    db.delete(like_row)
    db.commit()

    post.like_count = max(0, int(post.like_count or 0) - 1)
    db.add(post)
    db.commit()
    return None
