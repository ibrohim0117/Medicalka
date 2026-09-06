"""Fon vazifalari — eskirgan ma'lumotlarni tozalash.

Barchasi sinxron sessiya bilan ishlaydi (`app.db.sync_session`).
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, delete

from app.core.config import settings
from app.core.email import send_verification_email
from app.db.sync_session import session_scope
from app.models import Post, User, VerificationToken
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.cleanup_unverified_users")
def cleanup_unverified_users(older_than_hours: int | None = None) -> int:
    """Emailini tasdiqlamagan va muddati o'tgan hisoblarni o'chiradi.

    Mezon `users.created_at` bo'yicha: hisob yaratilganidan beri
    `UNVERIFIED_USER_TTL_HOURS` o'tgan bo'lsa va `is_verified` hali
    `false` bo'lsa, o'chiriladi.

    Postlari, izohlari va tokenlari `ON DELETE CASCADE` bilan birga
    o'chadi — alohida so'rov kerak emas.
    """
    soat = older_than_hours or settings.UNVERIFIED_USER_TTL_HOURS
    chegara = datetime.now(UTC) - timedelta(hours=soat)

    with session_scope() as session:
        # cast: session.execute() umumiy `Result` qaytaradi, DML uchun esa
        # bu aslida `CursorResult` va unda `rowcount` bor.
        natija = cast(
            CursorResult[Any],
            session.execute(
                delete(User).where(
                    User.is_verified.is_(False),
                    User.created_at < chegara,
                )
            ),
        )
        soni = natija.rowcount or 0

    logger.info("Tasdiqlanmagan hisoblar o'chirildi: %s ta (%s soatdan eski)", soni, soat)
    return soni


@celery_app.task(name="app.worker.tasks.cleanup_expired_tokens")
def cleanup_expired_tokens() -> int:
    """Muddati o'tgan va ishlatilgan tasdiqlash tokenlarini o'chiradi.

    Ular xavfsizlik uchun xatarli emas — servis har safar `expires_at`
    va `used_at` ni tekshiradi. Lekin jadval cheksiz o'sib boradi.
    """
    hozir = datetime.now(UTC)

    with session_scope() as session:
        natija = cast(
            CursorResult[Any],
            session.execute(
                delete(VerificationToken).where(
                    (VerificationToken.expires_at < hozir)
                    | (VerificationToken.used_at.is_not(None))
                )
            ),
        )
        soni = natija.rowcount or 0

    logger.info("Eskirgan tokenlar o'chirildi: %s ta", soni)
    return soni


@celery_app.task(name="app.worker.tasks.cleanup_old_posts")
def cleanup_old_posts(older_than_days: int | None = None) -> int:
    """`POST_TTL_DAYS` dan eski postlarni o'chiradi.

    Sozlama `0` bo'lsa vazifa hech narsa qilmaydi — bu standart holat.
    Postni o'chirish ma'lumot yo'qotish demak, shuning uchun u ochiq
    yoqilishi kerak.

    Izohlar va like'lar `ON DELETE CASCADE` bilan birga o'chadi.
    """
    kun = older_than_days if older_than_days is not None else settings.POST_TTL_DAYS
    if kun <= 0:
        logger.info("Post TTL o'chirilgan (POST_TTL_DAYS=%s), hech narsa qilinmadi", kun)
        return 0

    chegara = datetime.now(UTC) - timedelta(days=kun)

    with session_scope() as session:
        natija = cast(
            CursorResult[Any],
            session.execute(delete(Post).where(Post.created_at < chegara)),
        )
        soni = natija.rowcount or 0

    logger.info("Eski postlar o'chirildi: %s ta (%s kundan eski)", soni, kun)
    return soni


@celery_app.task(
    name="app.worker.tasks.send_verification_email_task",
    autoretry_for=(OSError,),
    retry_backoff=True,
    max_retries=3,
)
def send_verification_email_task(email: str, token: str) -> bool:
    """Tasdiqlash xatini fon vazifasi sifatida yuboradi.

    SMTP sekin va ishonchsiz bo'lishi mumkin — foydalanuvchi buni
    kutmasligi kerak. Tarmoq xatosida uch marta qayta uriniladi.
    """
    return send_verification_email(email, token)
