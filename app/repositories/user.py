"""Foydalanuvchi so'rovlari — faqat SQL/ORM, biznes-mantiq yo'q.

Bu yerda nima bo'ladi:
    * `UserRepository`: get, get_by_email, get_by_username,
      get_by_identifier (login uchun), email_exists, username_exists,
      list_users (qidiruv + paginatsiya), touch_last_login
    * `VerificationTokenRepository`: get_by_hash, invalidate_active, mark_used
"""

# TODO: from sqlalchemy import select
# TODO: from app.models.user import User
