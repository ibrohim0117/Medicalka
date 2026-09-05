"""Email tasdiqlash va parol tiklash tokenlari."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerificationTokenType(str, enum.Enum):
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ondelete="CASCADE": foydalanuvchi o'chirilsa tokenlari ham o'chadi,
    # aks holda baza tashqi kalit tufayli o'chirishga yo'l bermaydi.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Ochiq token bazada saqlanmaydi — faqat sha256 xeshi (64 belgi).
    # Baza o'g'irlansa ham tokenlardan foydalanib bo'lmaydi.
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # values_callable — busiz SQLAlchemy bazaga enum NOMINI ("EMAIL_VERIFY")
    # yozadi, biz esa qiymatini ("email_verify") kutamiz.
    type: Mapped[VerificationTokenType] = mapped_column(
        Enum(
            VerificationTokenType,
            name="verification_token_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=VerificationTokenType.EMAIL_VERIFY,
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # Ishlatilgan token qayta ishlatilmasin — o'chirmaymiz, belgilaymiz.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
