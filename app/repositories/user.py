"""Foydalanuvchi jadvaliga SQL so'rovlari. Biznes qoidalari bu yerda yo'q."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


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
