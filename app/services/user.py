"""Foydalanuvchi profili bilan bog'liq biznes-mantiq."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """Faqat yuborilgan maydonlarni o'zgartiradi (PATCH semantikasi).

        `None` qiymatlar tashlab yuboriladi: `username` bazada NOT NULL,
        uni `null` bilan tozalashga urinish IntegrityError berardi.
        """
        fields = {
            key: value
            for key, value in data.model_dump(exclude_unset=True).items()
            if value is not None
        }

        new_username = fields.get("username")
        if (
            new_username
            and new_username != user.username
            and await self.users.get_by_username(new_username)
        ):
            raise ConflictError("Bu username band", code="username_taken")

        for key, value in fields.items():
            setattr(user, key, value)
        await self.session.commit()
        return user
