"""Foydalanuvchi jadvaliga SQL so'rovlari. Biznes qoidalari bu yerda yo'q."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Post, User, VerificationToken


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_with_posts_and_likes(
        self, *, offset: int, limit: int
    ) -> tuple[Sequence[User], int]:
        """`/all` lentasi: foydalanuvchilar, postlari va like'lari.

        Uch daraja, lekin so'rovlar soni QAT'IY: COUNT + users + posts +
        likes = 4 ta. `selectinload` har bir darajani bitta
        `WHERE ... IN (...)` so'rovi bilan oladi, ya'ni 20 ta foydalanuvchi
        uchun ham, 100 ta uchun ham so'rovlar soni bir xil.

        Ketma-ket zanjir: avval postlar, keyin o'sha postlarning like'lari.
        """
        total = await self.session.scalar(select(func.count()).select_from(User)) or 0
        stmt = (
            select(User)
            .options(selectinload(User.posts).selectinload(Post.likes))
            .order_by(User.created_at.desc(), User.id.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return rows, total

    async def create(
        self, *, email: str, username: str, full_name: str, password_hash: str
    ) -> User:
        """Foydalanuvchi yaratadi va ID olish uchun flush qiladi.

        Commit qilmaydi — buni servis qatlami hal qiladi, chunki bitta
        amalda bir nechta yozuv bo'lishi mumkin (foydalanuvchi + tasdiqlash
        tokeni) va ular bitta tranzaksiyada ketishi kerak.
        """
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=password_hash,
        )
        self.session.add(user)
        await self.session.flush()
        return user


class VerificationTokenRepository:
    """Tasdiqlash tokenlari. Foydalanuvchi bilan chambarchas bog'liq,
    shuning uchun alohida fayl ochilmadi."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_token(self, token_hash: str) -> VerificationToken | None:
        stmt = select(VerificationToken).where(VerificationToken.token == token_hash)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> VerificationToken:
        token = VerificationToken(user_id=user_id, token=token_hash, expires_at=expires_at)
        self.session.add(token)
        await self.session.flush()
        return token
