"""Foydalanuvchi modeli."""

import uuid

from sqlalchemy import Boolean, String, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    # UUID'ni Python yaratadi (flush paytida, INSERT'ga qo'shib yuboriladi):
    # bazaga bog'liq emas va RETURNING kutilmaydi.
    # server_default — ilovadan tashqarida qilingan INSERT uchun zaxira.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # email va username alohida unique: birini o'zgartirish ikkinchisiga
    # ta'sir qilmaydi, login esa ikkalasi bilan ham ishlaydi.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    full_name: Mapped[str | None] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
