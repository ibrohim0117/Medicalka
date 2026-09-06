"""Email yuborish.

`SMTP_HOST` bo'sh bo'lsa xat yuborilmaydi — havola logga yoziladi.
Ishlab chiqishda va topshiriq doirasida shu yetarli, sozlash esa faqat
`.env` ni to'ldirishdan iborat.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def tasdiqlash_havolasi(token: str) -> str:
    return f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/auth/verify-email?token={token}"


def send_verification_email(email: str, token: str) -> bool:
    """Tasdiqlash xatini yuboradi. Yuborilgan bo'lsa `True`.

    Sinxron `smtplib` ishlatiladi, chunki bu funksiya Celery vazifasidan
    chaqiriladi — u yerda `await` yo'q.
    """
    havola = tasdiqlash_havolasi(token)

    if not settings.SMTP_HOST:
        logger.info("SMTP sozlanmagan. %s uchun havola: %s", email, havola)
        return False

    xat = EmailMessage()
    xat["Subject"] = "Medicalka Social — email manzilingizni tasdiqlang"
    xat["From"] = settings.SMTP_FROM
    xat["To"] = email
    xat.set_content(
        "Assalomu alaykum!\n\n"
        "Medicalka Social'da ro'yxatdan o'tganingiz uchun rahmat. "
        "Email manzilingizni tasdiqlash uchun quyidagi havolaga o'ting:\n\n"
        f"{havola}\n\n"
        f"Havola {settings.EMAIL_VERIFY_TTL_HOURS} soat amal qiladi.\n"
        "Agar siz ro'yxatdan o'tmagan bo'lsangiz, bu xatni e'tiborsiz qoldiring."
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_STARTTLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(xat)
    except Exception as exc:
        # Xat yuborilmasa ham ro'yxatdan o'tish bekor qilinmaydi:
        # foydalanuvchi keyin qayta so'rashi mumkin.
        logger.error("Tasdiqlash xati yuborilmadi (%s): %s", email, exc)
        return False

    logger.info("Tasdiqlash xati yuborildi: %s", email)
    return True
