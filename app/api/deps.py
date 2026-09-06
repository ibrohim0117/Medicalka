"""FastAPI dependency'lari — endpoint'lar shu yerdan sessiya va foydalanuvchi oladi."""

import secrets
import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_token
from app.db.session import get_session
from app.models import User
from app.repositories.user import UserRepository

# auto_error=False — sarlavha bo'lmasa FastAPI o'zi 403 tashlamasin.
# Xatoni o'zimiz beramiz, shunda javob shakli boshqa xatolar bilan bir xil.
_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
_CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


async def get_current_user(session: SessionDep, credentials: _CredentialsDep) -> User:
    """`Authorization: Bearer <token>` dan foydalanuvchini oladi."""
    if credentials is None:
        raise AuthError("Avtorizatsiya talab qilinadi", code="not_authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token muddati o'tgan", code="token_expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("Token yaroqsiz", code="invalid_token") from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise AuthError("Token yaroqsiz", code="invalid_token") from exc

    # Bazadan o'qish shart: token amal qilayotgan bo'lsa ham, foydalanuvchi
    # o'chirilgan bo'lishi mumkin.
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise AuthError("Foydalanuvchi topilmadi", code="user_not_found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_verified_user(user: CurrentUser) -> User:
    """Email tasdiqlangan bo'lishi shart bo'lgan endpoint'lar uchun."""
    if not user.is_verified:
        # 403, 401 emas: kim ekani ma'lum, qayta kirish yordam bermaydi.
        raise ForbiddenError("Avval email manzilingizni tasdiqlang", code="email_not_verified")
    return user


VerifiedUser = Annotated[User, Depends(get_verified_user)]


async def require_admin_token(
    x_admin_token: Annotated[str | None, Header(description="Admin siri")] = None,
) -> None:
    """Admin ruchkalari uchun umumiy sir bilan himoya.

    To'liq admin autentifikatsiyasi emas — texnik tugma. `compare_digest`
    ishlatiladi: oddiy `==` birinchi farqli belgida to'xtaydi va javob
    vaqti orqali sirni belgi-belgi topish mumkin bo'lardi.
    """
    if x_admin_token is None:
        raise AuthError("X-Admin-Token sarlavhasi kerak", code="admin_token_required")
    if not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise ForbiddenError("Admin token noto'g'ri", code="invalid_admin_token")


AdminOnly = Depends(require_admin_token)
