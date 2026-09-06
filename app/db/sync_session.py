"""Sinxron engine — Celery worker'lari uchun.

Celery vazifalari oddiy funksiyalar, ular `await` qila olmaydi. Shuning
uchun ilovaning asyncpg engine'i o'rniga alohida psycopg2 engine ishlatiladi.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# NullPool: Celery prefork rejimida ishlaydi va jarayonni fork qiladi.
# Ochiq ulanishlar fork'dan keyin bola jarayonlarda buzilgan holatda
# qoladi. Har bir vazifa yangi ulanish oladi — davriy vazifalar uchun
# bu arzon narx.
sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.DB_ECHO,
    poolclass=NullPool,
)

SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Tranzaksiyani o'rab turuvchi kontekst menejeri.

    Muvaffaqiyatli tugasa commit, xatolikda rollback qiladi. Vazifa
    yarim bajarilgan holatda qolmaydi.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
