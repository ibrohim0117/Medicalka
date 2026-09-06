"""Izoh endpoint'lari — `/posts/{post_id}/comments`."""

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import SessionDep, VerifiedUser
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.common import Page, PaginationDep
from app.services.comment import CommentService

router = APIRouter(prefix="/posts", tags=["comments"])


@router.get(
    "/{post_id}/comments",
    response_model=Page[CommentRead],
    summary="Post izohlari",
)
async def list_comments(
    post_id: uuid.UUID, session: SessionDep, params: PaginationDep
) -> Page[CommentRead]:
    """Eski izohdan boshlab. Avtorizatsiya talab qilinmaydi."""
    comments, total = await CommentService(session).list_for_post(post_id, params)
    return Page.create([CommentRead.model_validate(c) for c in comments], total, params)


@router.post(
    "/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Izoh qoldirish",
)
async def create_comment(
    post_id: uuid.UUID, data: CommentCreate, user: VerifiedUser, session: SessionDep
) -> CommentRead:
    """Email tasdiqlangan bo'lishi shart."""
    comment = await CommentService(session).create(post_id, user, data)
    return CommentRead.model_validate(comment)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Izohni o'chirish",
)
async def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    user: VerifiedUser,
    session: SessionDep,
) -> Response:
    """Faqat izoh muallifi. Post egasi ham o'chira olmaydi."""
    await CommentService(session).delete(post_id, comment_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
