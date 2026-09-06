"""Foydalanuvchi modeli."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.like import Like
    from app.models.post import Post
    from app.models.verification import VerificationToken


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

    # lazy="raise" — bog'lanishga oldindan yuklamasdan murojaat qilinsa
    # xato tashlaydi. passive_deletes=True — o'chirishni bazaning
    # ON DELETE CASCADE'iga qoldiradi, SQLAlchemy bolalarni yuklamaydi.
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    likes: Mapped[list["Like"]] = relationship(
        back_populates="user",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        back_populates="user",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
