"""Parol xeshlash (argon2) va JWT tokenlar."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

TokenType = Literal["access", "refresh"]

# Standart parametrlar RFC 9106 tavsiyasiga yaqin: 64 MiB xotira, 3 o'tish.
# Xotira talabi GPU'da parallel hujumni qimmatga tushiradi — argon2 ning
# bcrypt'dan asosiy afzalligi shunda.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Parolni argon2 bilan xeshlaydi. Tuz xesh ichiga yoziladi."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Parol xeshga mos kelishini tekshiradi.

    argon2 mos kelmasa istisno tashlaydi; biz uni `False` ga aylantiramiz,
    chunki chaqiruvchi uchun "noto'g'ri parol" va "buzuq xesh" bir xil natija.

    Ikkita istisno kerak: VerificationError parol mos kelmaganda,
    InvalidHashError esa xesh buzuq bo'lganda. Ikkinchisi ValueError'dan
    meros oladi, Argon2Error'dan emas — bitta `except` yetarli emas.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _create_token(subject: str, token_type: TokenType, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        # Har bir token noyob bo'lsin. Usiz bir soniya ichida berilgan
        # ikkita token bayt-baytga bir xil chiqadi — sessiyalarni
        # ajratib bo'lmaydi va kelajakda bekor qilish ro'yxati tuzib
        # bo'lmaydi.
        "jti": uuid.uuid4().hex,
        # Tur talab qilinadi: refresh tokenni access o'rnida ishlatib
        # bo'lmasin, aks holda uzoq muddatli token qisqasini almashtiradi.
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(subject, "access", timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES))


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS))


def decode_token(token: str, expected_type: TokenType = "access") -> dict[str, Any]:
    """Tokenni ochadi va tekshiradi.

    Raises:
        jwt.PyJWTError: imzo noto'g'ri, muddati o'tgan yoki turi mos kelmasa.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "type", "exp"]},
    )
    if payload["type"] != expected_type:
        raise jwt.InvalidTokenError(
            f"'{expected_type}' turidagi token kutilgan edi, '{payload['type']}' keldi"
        )
    return payload


def generate_verification_token() -> str:
    """Email tasdiqlash uchun bir martalik tasodifiy token (ochiq matn)."""
    return secrets.token_urlsafe(32)


def hash_verification_token(token: str) -> str:
    """Bazada saqlanadigan sha256 xeshi — 64 belgi.

    Parol emas, shuning uchun argon2 kerak emas: token allaqachon tasodifiy
    va uzun, uni lug'at bo'yicha topib bo'lmaydi. Xeshlash esa baza sizib
    chiqqanda tokenlardan foydalanishning oldini oladi.
    """
    return hashlib.sha256(token.encode()).hexdigest()
