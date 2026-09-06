"""Like endpoint'lari — `/posts/{post_id}/like`."""

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.like import LikeRead
from app.services.like import LikeService

router = APIRouter(prefix="/posts", tags=["likes"])


@router.post(
    "/{post_id}/like",
    response_model=LikeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Postga like qo'yish",
)
async def like_post(post_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> LikeRead:
    """`CurrentUser`, `VerifiedUser` emas — talabda tasdiqlanmagan
    foydalanuvchi ham like bosa oladi deyilgan.

    O'z postiga 403, takroriy like'ga 409 qaytadi.
    """
    like = await LikeService(session).like(post_id, user)
    return LikeRead.model_validate(like)


@router.delete(
    "/{post_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Like'ni olib tashlash",
)
async def unlike_post(post_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await LikeService(session).unlike(post_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
