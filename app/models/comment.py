"""Izoh modeli."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class Comment(Base):
    __tablename__ = "comments"
    # Asosiy so'rov: bitta postning izohlari, vaqt bo'yicha tartibda.
    # Birinchi ustun post_id bo'lgani uchun bu indeks post_id bo'yicha
    # oddiy qidiruvga ham xizmat qiladi — alohida indeks kerak emas.
    __table_args__ = (Index("ix_comments_post_id_created_at", "post_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Post yoki muallif o'chirilsa izoh ham o'chadi.
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Uzunlik talab bo'yicha: 2 000 belgigacha.
    content: Mapped[str] = mapped_column(String(2_000))

    # TimestampMixin ishlatilmadi — topshiriqda izoh uchun faqat created_at
    # so'ralgan, updated_at yo'q.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["Post"] = relationship(back_populates="comments", lazy="raise")
    author: Mapped["User"] = relationship(back_populates="comments", lazy="raise")
