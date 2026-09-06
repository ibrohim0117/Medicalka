"""Post jadvaliga SQL so'rovlari."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Post


def _like_naqsh(matn: str) -> str:
    """Foydalanuvchi kiritgan matnni LIKE naqshiga aylantiradi.

    `%` va `_` — LIKE ning maxsus belgilari. Ularni qochirmasak, "50%"
    deb qidirilganda hamma narsa topilardi, "a_b" esa "axb" ni ham
    topardi. `\\` birinchi almashtiriladi, aks holda o'zi qo'shgan
    qochirish belgilarini qayta qochirardik.
    """
    for belgi in ("\\", "%", "_"):
        matn = matn.replace(belgi, f"\\{belgi}")
    return f"%{matn}%"


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

    async def list_posts(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[Sequence[Post], int]:
        """Sahifalangan ro'yxat va jami soni.

        Ikkita so'rov: bittasi qatorlar, bittasi COUNT. Bu N+1 emas —
        so'rovlar soni sahifadagi elementlarga bog'liq emas.

        Shartlar bir marta tuziladi va IKKALA so'rovga ham qo'llanadi:
        aks holda `total` filtrlanmagan songa teng bo'lib qolardi.
        """
        shartlar: list[ColumnElement[bool]] = []
        if search and search.strip():
            naqsh = _like_naqsh(search.strip())
            # ILIKE — registrga sezgir emas: "Yurak" so'rovi "yurak" ni ham topadi.
            shartlar.append(
                or_(
                    Post.title.ilike(naqsh, escape="\\"),
                    Post.content.ilike(naqsh, escape="\\"),
                )
            )
        # Ikki chegara ham kiritilgan: >= va <=.
        if date_from is not None:
            shartlar.append(Post.created_at >= date_from)
        if date_to is not None:
            shartlar.append(Post.created_at <= date_to)

        total = (
            await self.session.scalar(select(func.count()).select_from(Post).where(*shartlar)) or 0
        )
        stmt = (
            select(Post)
            .where(*shartlar)
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
