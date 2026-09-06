"""Autentifikatsiya biznes-mantig'i: ro'yxatdan o'tish, kirish, tasdiqlash."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AppError,
    AuthError,
    ConflictError,
    InvalidTokenError,
)
from app.core.rate_limit import LoginRateLimiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
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
logger = logging.getLogger(__name__)

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

        # Xat navbatga qo'yiladi — SMTP javobini foydalanuvchi kutmaydi.
        # Import shu yerda: modul darajasida bo'lsa aylanma import chiqadi
        # (tasks -> services -> tasks).
        from app.worker.tasks import send_verification_email_task

        try:
            send_verification_email_task.delay(user.email, raw_token)
        except Exception as exc:
            logger.warning("Tasdiqlash xati navbatga qo'yilmadi: %s", exc)
        return user, raw_token

    async def login(self, data: UserLogin, ip: str = "unknown") -> tuple[str, str]:
        """Access va refresh tokenlarni qaytaradi.

        Email ham, username ham qabul qilinadi.
        """
        limiter = LoginRateLimiter()
        if await limiter.bloklanganmi(ip, data.login):
            raise AppError(
                "Juda ko'p urinish. Birozdan keyin qayta harakat qiling",
                code="too_many_attempts",
                status_code=429,
            )

        user = (
            await self.users.get_by_email(data.login)
            if "@" in data.login
            else await self.users.get_by_username(data.login)
        )
        # Foydalanuvchi topilmasa ham xeshlash bajariladi (vaqt bo'yicha hujum).
        if not verify_password(data.password, user.password_hash if user else _SOXTA_XESH):
            await limiter.muvaffaqiyatsiz(ip, data.login)
            raise AuthError("Login yoki parol noto'g'ri", code="invalid_credentials")
        # `user` bu yerda albatta mavjud: soxta xesh hech qachon mos kelmaydi.
        assert user is not None
        await limiter.tozalash(ip, data.login)
        return self._issue_tokens(user)

    async def refresh(self, raw_token: str) -> tuple[str, str]:
        """Refresh token evaziga yangi juftlik beradi.

        Eslatma: eski refresh token o'z muddati tugagunicha yaroqli
        bo'lib qoladi — bekor qilingan tokenlar ro'yxati yo'q. To'liq
        himoya uchun `jti` ni Redis'da saqlash kerak bo'lardi.
        """
        try:
            payload = decode_token(raw_token, expected_type="refresh")
            user_id = uuid.UUID(payload["sub"])
        except (jwt.PyJWTError, ValueError) as exc:
            raise AuthError(
                "Refresh token yaroqsiz yoki muddati o'tgan",
                code="invalid_refresh_token",
            ) from exc

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AuthError("Foydalanuvchi topilmadi", code="user_not_found")
        return self._issue_tokens(user)

    @staticmethod
    def _issue_tokens(user: User) -> tuple[str, str]:
        return create_access_token(str(user.id)), create_refresh_token(str(user.id))

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
