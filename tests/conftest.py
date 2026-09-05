"""Test fixture'lari.

Testlar haqiqiy Postgres'ga qarshi ishlaydi — loyihada SQLite yo'q,
shuning uchun testdagi xatti-harakat ishlab chiqarishdagi bilan bir xil.

Bu yerda nima bo'ladi:
    * Muhitni testga o'tkazish (JWT_SECRET, DATABASE_URL — alohida test bazasi)
      — `app.core.config` import qilinishidan OLDIN
    * `engine` — alohida test bazasi, `Base.metadata.create_all`
    * `session` — har bir test uchun tranzaksiya, oxirida rollback
    * `client` — `get_session` dependency almashtirilgan httpx AsyncClient
    * `user_payload`, `registered_user`, `auth_headers`

Ishga tushirish uchun `docker compose up -d db` yetarli.
"""

# TODO: import pytest
# TODO: from httpx import ASGITransport, AsyncClient
