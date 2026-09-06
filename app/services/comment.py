"""Izoh biznes-mantig'i."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Comment, User
from app.repositories.comment import CommentRepository
from app.repositories.post import PostRepository
from app.schemas.comment import CommentCreate
from app.schemas.common import PaginationParams


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.posts = PostRepository(session)

    async def list_for_post(
        self, post_id: uuid.UUID, params: PaginationParams
    ) -> tuple[Sequence[Comment], int]:
        await self._require_post(post_id)
        return await self.comments.list_for_post(post_id, offset=params.offset, limit=params.size)

    async def create(self, post_id: uuid.UUID, user: User, data: CommentCreate) -> Comment:
        await self._require_post(post_id)
        comment = await self.comments.create(
            post_id=post_id, author_id=user.id, content=data.content
        )
        await self.session.commit()
        return comment

    async def delete(self, post_id: uuid.UUID, comment_id: uuid.UUID, user: User) -> None:
        comment = await self.comments.get_by_id(comment_id)
        if comment is None or comment.post_id != post_id:
            # Boshqa postning izohi berilsa ham "topilmadi" — yo'l noto'g'ri.
            raise NotFoundError("Izoh topilmadi")
        # Faqat izoh muallifi. Post egasi ham o'chira olmaydi — talab shunday.
        if comment.author_id != user.id:
            raise ForbiddenError("Bu izoh sizga tegishli emas")
        await self.comments.delete(comment)
        await self.session.commit()

    async def _require_post(self, post_id: uuid.UUID) -> None:
        """Mavjud bo'lmagan postga izoh yozib ham, o'qib ham bo'lmaydi."""
        if await self.posts.get_by_id(post_id) is None:
            raise NotFoundError("Post topilmadi")
