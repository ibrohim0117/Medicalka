"""Autentifikatsiya biznes-mantig'i.

Bu yerda nima bo'ladi:
    * `register` — email/username bandligini tekshirish, parolni xeshlash,
      email tasdiqlash token'ini yaratish
    * `authenticate` / `login` — parolni tekshirish, token'lar berish
    * `refresh` — refresh token orqali yangi access token
    * `verify_email`, `resend_verification`
    * `change_password`
"""

# TODO: from app.repositories.user import UserRepository
