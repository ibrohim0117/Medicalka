"""Test fixture'lari.

Bu yerda nima bo'ladi:
    * Muhitni testga o'tkazish (SECRET_KEY, DATABASE_URL=sqlite+aiosqlite)
      — `app.core.config` import qilinishidan OLDIN
    * `engine` — xotiradagi SQLite, `Base.metadata.create_all`
    * `session` — testlar uchun AsyncSession
    * `client` — `get_session` dependency almashtirilgan httpx AsyncClient
    * `user_payload`, `registered_user`, `auth_headers`
"""

# TODO: import pytest
# TODO: from httpx import ASGITransport, AsyncClient
