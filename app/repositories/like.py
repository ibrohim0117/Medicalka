"""Like jadvaliga SQL so'rovlari."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Like


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> Like | None:
        """`(user_id, post_id)` unique indeksi shu so'rovni to'liq qoplaydi."""
        stmt = select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> Like:
        like = Like(user_id=user_id, post_id=post_id)
        self.session.add(like)
        await self.session.flush()
        return like

    async def delete(self, like: Like) -> None:
        await self.session.delete(like)
