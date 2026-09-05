"""FastAPI dependency'lari.

Bu yerda nima bo'ladi:
    * `SessionDep` — `get_session` (app.db.session)
    * `get_current_user` — Bearer token'dan foydalanuvchini olish
    * `get_current_user_optional` — mehmonlar ham ko'radigan endpoint'lar uchun
    * `get_verified_user`, `get_superuser`
    * Servis dependency'lari: auth / post / comment / like
    * `PaginationDep`
"""

# TODO: from fastapi.security import HTTPBearer
# TODO: from app.db.session import get_session
