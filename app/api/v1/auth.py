"""`/auth` endpoint'lari.

Endpoint'lar:
    POST /auth/register              — ro'yxatdan o'tish
    POST /auth/login                 — kirish (email yoki username)
    POST /auth/refresh               — access token'ni yangilash
    POST /auth/verify-email          — emailni tasdiqlash
    POST /auth/resend-verification   — tasdiqlash xatini qayta yuborish
    POST /auth/change-password       — parolni almashtirish
    GET  /auth/me                    — joriy foydalanuvchi
"""

# TODO: from fastapi import APIRouter
# router = APIRouter(prefix="/auth", tags=["auth"])
