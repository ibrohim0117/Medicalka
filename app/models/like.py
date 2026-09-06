"""Like modeli — bir foydalanuvchi bitta postga faqat bir marta."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Like(Base):
    __tablename__ = "likes"
    # Takrorlanishni baza darajasida to'xtatamiz. Faqat kodda tekshirish
    # yetarli emas: ikki so'rov bir vaqtda kelsa ikkalasi ham "hali like
    # yo'q" deb ko'radi va ikkita qator yozadi.
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_likes_user_id_post_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # user_id uchun alohida indeks kerak emas — u UniqueConstraint
    # indeksining birinchi ustuni.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # post_id esa ikkinchi ustun, shuning uchun o'z indeksiga muhtoj:
    # "shu postga nechta like" so'rovi uchun.
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
