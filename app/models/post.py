"""Post (e'lon) modeli."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.like import Like
    from app.models.user import User


class Post(Base, TimestampMixin):
    __tablename__ = "posts"
    # Lenta yangi postlardan boshlab o'qiladi (ORDER BY created_at DESC).
    # Indeksisiz Postgres har safar butun jadvalni saralaydi.
    __table_args__ = (Index("ix_posts_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Muallif o'chirilsa postlari ham o'chadi.
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Uzunliklar talab bo'yicha: title 255 gacha, content 10 000 gacha.
    # Quyi chegara (title 5 belgi) Pydantic sxemasida tekshiriladi.
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(10_000))

    author: Mapped["User"] = relationship(back_populates="posts", lazy="raise")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    likes: Mapped[list["Like"]] = relationship(
        back_populates="post",
        lazy="raise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
