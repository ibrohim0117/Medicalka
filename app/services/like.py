"""Like biznes-mantig'i."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import Like, User
from app.repositories.like import LikeRepository
from app.repositories.post import PostRepository


class LikeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.likes = LikeRepository(session)
        self.posts = PostRepository(session)

    async def like(self, post_id: uuid.UUID, user: User) -> Like:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post topilmadi")
        # Post baribir yuklandi, ya'ni bu tekshiruv qo'shimcha so'rovsiz.
        if post.author_id == user.id:
            raise ForbiddenError("O'z postingizga like bosa olmaysiz", code="self_like")
        if await self.likes.get(user_id=user.id, post_id=post_id) is not None:
            raise ConflictError("Siz allaqachon like bosgansiz", code="already_liked")

        try:
            like = await self.likes.create(user_id=user.id, post_id=post_id)
            await self.session.commit()
        except IntegrityError as exc:
            # Yuqoridagi tekshiruv bilan INSERT orasida boshqa so'rov ulgurdi.
            # Bazadagi uq_likes_user_id_post_id oxirgi to'siq bo'lib turadi.
            await self.session.rollback()
            raise ConflictError("Siz allaqachon like bosgansiz", code="already_liked") from exc
        return like

    async def unlike(self, post_id: uuid.UUID, user: User) -> None:
        like = await self.likes.get(user_id=user.id, post_id=post_id)
        if like is None:
            raise NotFoundError("Like topilmadi", code="like_not_found")
        await self.likes.delete(like)
        await self.session.commit()
