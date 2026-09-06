"""Autentifikatsiya biznes-mantig'i: ro'yxatdan o'tish, kirish, tasdiqlash."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError, ConflictError, InvalidTokenError
from app.core.security import (
    create_access_token,
    generate_verification_token,
    hash_password,
    hash_verification_token,
    verify_password,
)
from app.models import User
from app.repositories.user import UserRepository, VerificationTokenRepository
from app.schemas.user import UserCreate, UserLogin

# Foydalanuvchi topilmaganda ham parol tekshiriladi — aks holda javob vaqti
# hisobning mavjudligini oshkor qilardi (topilmasa tez, topilsa 33 ms).
_SOXTA_XESH = hash_password("mavjud-bo'lmagan-parol")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tokens = VerificationTokenRepository(session)

    async def register(self, data: UserCreate) -> tuple[User, str]:
        """Foydalanuvchi va tasdiqlash tokenini yaratadi.

        Ochiq tokenni qaytaradi — u bazada saqlanmaydi, faqat xeshi.
        SMTP yo'q, shuning uchun uni chaqiruvchi qatlam foydalanuvchiga
        yetkazadi.
        """
        if await self.users.get_by_email(data.email):
            raise ConflictError("Bu email allaqachon ro'yxatdan o'tgan", code="email_taken")
        if await self.users.get_by_username(data.username):
            raise ConflictError("Bu username band", code="username_taken")

        user = await self.users.create(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
        )
        raw_token = generate_verification_token()
        await self.tokens.create(
            user_id=user.id,
            token_hash=hash_verification_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.EMAIL_VERIFY_TTL_HOURS),
        )
        # Ikkala yozuv bitta tranzaksiyada: tokensiz foydalanuvchi qolmasin.
        await self.session.commit()
        return user, raw_token

    async def login(self, data: UserLogin) -> str:
        """Access token qaytaradi. Email ham, username ham qabul qilinadi."""
        user = (
            await self.users.get_by_email(data.login)
            if "@" in data.login
            else await self.users.get_by_username(data.login)
        )
        # Foydalanuvchi topilmasa ham xeshlash bajariladi (vaqt bo'yicha hujum).
        if not verify_password(data.password, user.password_hash if user else _SOXTA_XESH):
            raise AuthError("Login yoki parol noto'g'ri", code="invalid_credentials")
        # `user` bu yerda albatta mavjud: soxta xesh hech qachon mos kelmaydi.
        assert user is not None
        return create_access_token(str(user.id))

    async def verify_email(self, raw_token: str) -> User:
        """Tokenni tekshiradi va foydalanuvchini tasdiqlangan deb belgilaydi."""
        token = await self.tokens.get_by_token(hash_verification_token(raw_token))
        if token is None:
            raise InvalidTokenError("Tasdiqlash tokeni topilmadi")
        if token.used_at is not None:
            raise InvalidTokenError("Bu havola allaqachon ishlatilgan", code="token_used")
        if token.expires_at < datetime.now(UTC):
            raise InvalidTokenError("Havola muddati o'tgan", code="token_expired")

        user = await self.users.get_by_id(token.user_id)
        if user is None:
            raise InvalidTokenError("Tokenga tegishli foydalanuvchi topilmadi")

        user.is_verified = True
        token.used_at = datetime.now(UTC)
        await self.session.commit()
        return user
