"""Foydalanuvchi va autentifikatsiya sxemalari."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_PATTERN = r"^[A-Za-z0-9_]+$"

# `[^\W\d_]` — harf (lotin ham, kirill ham), lekin raqam va pastki chiziq emas.
#
# Apostrof harflar orasida ruxsat etilgan: o'zbek lotinida u alifboning bir
# qismi (O'ktam, G'ulom, Sa'dulla). Uchta belgi qabul qilinadi — oddiy ' va
# ikkita tipografik variant (ʻ ʼ), chunki klaviaturaga qarab har xil keladi.
#
# Apostroflarni harf sinfidan alohida chiqaramiz: ʻ va ʼ Unicode'da Lm
# (modifier letter) turkumida, ya'ni `[^\W\d_]` ularni harf deb qabul qiladi
# va "ʼAli" kabi noto'g'ri joylashuv o'tib ketardi.
_HARF = r"[^\W\d_'\u02bb\u02bc]"
# So'z: harf bilan boshlanadi va tugaydi, apostrof faqat harflar orasida.
# So'zlar bo'shliq yoki defis bilan ajratiladi.
_SOZ = rf"{_HARF}+(?:['\u02bb\u02bc]{_HARF}+)*"
_FULL_NAME_RE = re.compile(rf"^{_SOZ}(?:[ -]{_SOZ})*$", re.UNICODE)


def _clean_full_name(value: str) -> str:
    cleaned = value.strip()
    if not _FULL_NAME_RE.match(cleaned):
        raise ValueError("full_name faqat harflar, bo'shliq va defisdan iborat bo'lishi kerak")
    return cleaned


class UserCreate(BaseModel):
    """POST /auth/register kirishi."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)
    full_name: str = Field(min_length=2, max_length=100)
    # Yuqori chegara ham kerak: argon2 xeshlash qimmat amal, cheksiz uzun
    # parol serverga yuk bo'lib qolmasin.
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", "username", mode="after")
    @classmethod
    def to_lowercase(cls, value: str) -> str:
        """Registr farqi hisobga olinmasin: Ali va ali bitta nom."""
        return value.lower()

    @field_validator("full_name", mode="after")
    @classmethod
    def check_full_name(cls, value: str) -> str:
        return _clean_full_name(value)


class UserLogin(BaseModel):
    """POST /auth/login kirishi. `login` maydoniga email ham, username ham bo'ladi."""

    login: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("login", mode="after")
    @classmethod
    def to_lowercase(cls, value: str) -> str:
        return value.strip().lower()


class UserUpdate(BaseModel):
    """PATCH /users/me kirishi — faqat yuborilgan maydonlar o'zgaradi."""

    username: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=USERNAME_PATTERN
    )
    full_name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("username", mode="after")
    @classmethod
    def to_lowercase(cls, value: str | None) -> str | None:
        return value.lower() if value else value

    @field_validator("full_name", mode="after")
    @classmethod
    def check_full_name(cls, value: str | None) -> str | None:
        return _clean_full_name(value) if value else value


class UserRead(BaseModel):
    """Javoblarda qaytadigan foydalanuvchi. password_hash bu yerda YO'Q."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None
    is_verified: bool
    created_at: datetime


class Token(BaseModel):
    """POST /auth/login va POST /auth/refresh javobi."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """POST /auth/refresh kirishi."""

    refresh_token: str = Field(min_length=16)


class RegisterResponse(BaseModel):
    """POST /auth/register javobi."""

    user: UserRead
    # SMTP yo'q, shuning uchun tokenni javobda qaytaramiz. Ishlab
    # chiqarishda bu xavfli — u yerda `None` bo'ladi va emailga yuboriladi.
    verification_token: str | None = None
