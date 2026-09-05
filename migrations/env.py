"""Alembic muhiti.

Bu yerda nima bo'ladi:
    * `config.set_main_option("sqlalchemy.url", settings.sync_database_url)`
    * `import app.models` — autogenerate jadvallarni ko'rishi uchun
    * `target_metadata = Base.metadata`
    * `run_migrations_offline()` / `run_migrations_online()`

Buyruqlar:
    alembic revision --autogenerate -m "izoh"
    alembic upgrade head
"""

# TODO: from alembic import context
# TODO: from app.core.config import settings
# TODO: from app.db.base import Base
