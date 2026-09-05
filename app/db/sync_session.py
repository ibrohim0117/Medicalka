"""Sinxron engine — Celery worker'lari uchun.

Celery vazifalari oddiy (sinxron) funksiyalar, shuning uchun ular asyncpg
emas, psycopg2 orqali ishlaydi.

Bu yerda nima bo'ladi:
    * `sync_engine = create_engine(settings.sync_database_url, ...)`
    * `SessionLocal = sessionmaker(bind=sync_engine, ...)`
    * `session_scope()` — commit/rollback qiluvchi kontekst menejeri
"""

# TODO: from sqlalchemy import create_engine
# TODO: from sqlalchemy.orm import sessionmaker
