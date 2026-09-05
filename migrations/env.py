"""Alembic muhiti — sozlamalar app.core.config dan olinadi."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  — autogenerate jadvallarni shundan ko'radi
from app.core.config import settings
from app.db.base import Base

config = context.config

# alembic.ini da sqlalchemy.url yozilmagan — u shu yerda .env dan qo'yiladi.
# Alembic sinxron ishlaydi, shuning uchun psycopg2 varianti.
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """`--sql` rejimi: bazaga ulanmasdan SQL matnini chiqaradi."""
    context.configure(
        url=settings.sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Bazaga ulanib migratsiyalarni qo'llaydi."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # ustun turi o'zgarsa ham sezadi
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
