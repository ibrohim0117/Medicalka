"""Alembic muhiti — async engine, sozlamalar app.core.config dan."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.models  # noqa: F401  — autogenerate jadvallarni shundan ko'radi
from app.core.config import settings
from app.db.base import Base

config = context.config

# alembic.ini da sqlalchemy.url yozilmagan — u shu yerda .env dan qo'yiladi.
# `%` ni ikkilantiramiz: set_main_option qiymatni ConfigParser orqali
# o'tkazadi va yolg'iz `%` ni format belgisi deb o'ylaydi (parolda uchrashi mumkin).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """`--sql` rejimi: bazaga ulanmasdan SQL matnini chiqaradi."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Migratsiyalarni bajaradi. Alembic sinxron API, shuning uchun bu
    funksiya `run_sync` orqali async ulanish ustida ishlatiladi."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # ustun turi o'zgarsa ham sezadi
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # bir martalik jarayon, hovuz kerak emas
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
