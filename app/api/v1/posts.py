"""`/posts` endpoint'lari."""

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import SessionDep, VerifiedUser
from app.schemas.comment import CommentRead
from app.schemas.common import Page, PaginationDep
from app.schemas.post import (
    PostCreate,
    PostDetail,
    PostFiltersDep,
    PostRead,
    PostUpdate,
)
from app.services.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=Page[PostRead], summary="Postlar ro'yxati")
async def list_posts(
    session: SessionDep, params: PaginationDep, filters: PostFiltersDep
) -> Page[PostRead]:
    """Barcha postlar, yangisidan boshlab. Avtorizatsiya talab qilinmaydi."""
    posts, total = await PostService(session).list_posts(params, filters)
    return Page.create([PostRead.model_validate(p) for p in posts], total, params)


@router.post(
    "",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post yaratish",
)
async def create_post(data: PostCreate, user: VerifiedUser, session: SessionDep) -> PostRead:
    """Email tasdiqlangan bo'lishi shart — `VerifiedUser` shuni ta'minlaydi."""
    post = await PostService(session).create(user, data)
    return PostRead.model_validate(post)


@router.get("/{post_id}", response_model=PostDetail, summary="Post va izohlari")
async def get_post(post_id: uuid.UUID, session: SessionDep) -> PostDetail:
    post = await PostService(session).get_detail(post_id)
    return PostDetail(
        **PostRead.model_validate(post).model_dump(),
        comments=[CommentRead.model_validate(c) for c in post.comments],
    )


@router.patch("/{post_id}", response_model=PostRead, summary="Postni tahrirlash")
async def update_post(
    post_id: uuid.UUID, data: PostUpdate, user: VerifiedUser, session: SessionDep
) -> PostRead:
    """Faqat muallif. Begona post uchun 403, mavjud bo'lmasa 404."""
    post = await PostService(session).update(post_id, user, data)
    return PostRead.model_validate(post)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Postni o'chirish",
)
async def delete_post(post_id: uuid.UUID, user: VerifiedUser, session: SessionDep) -> Response:
    """Faqat muallif. Izohlar va like'lar CASCADE bilan birga o'chadi."""
    await PostService(session).delete(post_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
