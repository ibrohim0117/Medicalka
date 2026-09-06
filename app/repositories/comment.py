"""Izoh jadvaliga SQL so'rovlari."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def list_for_post(
        self, post_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[Comment], int]:
        """Postning izohlari, eskisidan boshlab.

        Ikkita so'rov: COUNT va sahifadagi qatorlar. Izohlar soni qancha
        bo'lsa ham so'rovlar soni o'zgarmaydi.
        """
        total = (
            await self.session.scalar(
                select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
            )
            or 0
        )
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            # Suhbat tartibi: eski izoh yuqorida. `id` — barqaror tartib uchun.
            # `(post_id, created_at)` indeksi shu so'rovni to'liq qoplaydi.
            .order_by(Comment.created_at.asc(), Comment.id.asc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return rows, total

    async def create(self, *, post_id: uuid.UUID, author_id: uuid.UUID, content: str) -> Comment:
        comment = Comment(post_id=post_id, author_id=author_id, content=content)
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def delete(self, comment: Comment) -> None:
        await self.session.delete(comment)
