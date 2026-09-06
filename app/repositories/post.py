"""Post jadvaliga SQL so'rovlari."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Post


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        return await self.session.get(Post, post_id)

    async def get_with_comments(self, post_id: uuid.UUID) -> Post | None:
        """Post va uning izohlari — ikkita so'rovda, N+1 siz.

        `selectinload` izohlarni alohida `WHERE post_id IN (...)` so'rovi
        bilan oladi. Usiz `post.comments` ga murojaat `lazy="raise"` ga
        urilardi.
        """
        stmt = select(Post).options(selectinload(Post.comments)).where(Post.id == post_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_posts(self, *, offset: int, limit: int) -> tuple[Sequence[Post], int]:
        """Sahifalangan ro'yxat va jami soni.

        Ikkita so'rov: bittasi qatorlar, bittasi COUNT. Bu N+1 emas —
        so'rovlar soni sahifadagi elementlarga bog'liq emas.
        """
        total = await self.session.scalar(select(func.count()).select_from(Post)) or 0
        stmt = (
            select(Post)
            # `id` ikkinchi mezon: bir xil vaqtli postlar tartibi barqaror
            # bo'lsin, aks holda sahifalar orasida element takrorlanishi mumkin.
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return rows, total

    async def create(self, *, author_id: uuid.UUID, title: str, content: str) -> Post:
        post = Post(author_id=author_id, title=title, content=content)
        self.session.add(post)
        await self.session.flush()
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
