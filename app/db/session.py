"""Async engine va sessiya fabrikasi — FastAPI uchun."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # uzilgan ulanishni ishlatishdan oldin tekshiradi
)

# expire_on_commit=False: commit'dan keyin obyektlarni qayta yuklamaydi,
# async'da bu "greenlet" xatosiga olib kelardi.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — bitta so'rovga bitta sessiya.

    `async with` chiqishda sessiyani yopadi; commit qilinmagan
    tranzaksiya o'z-o'zidan bekor bo'ladi.
    """
    async with AsyncSessionLocal() as session:
        yield session
