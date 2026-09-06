"""Test fixture'lari.

Testlar haqiqiy Postgres'ga qarshi ishlaydi — loyihada SQLite yo'q,
shuning uchun testdagi xatti-harakat ishlab chiqarishdagi bilan bir xil
(CHECK, CASCADE, ILIKE, timestamptz SQLite'da boshqacha ishlaydi).

Izolyatsiya tranzaksiya orqali: har bir test ochiq tranzaksiya ichida
ishlaydi va oxirida rollback qilinadi. Jadvallar qayta yaratilmaydi,
shuning uchun tez.
"""

import os

# Sozlamalar import qilinishidan OLDIN muhitni testga o'tkazamiz.
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://medicalka:medicalka@localhost:5432/medicalka_test",
)
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-kamida-o-ttiz-ikki-belgi-bolsin")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token-16+")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")
# Vazifalar broker'siz, o'sha yerda bajariladi — testlar Redis talab qilmaydi.
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

from collections.abc import AsyncGenerator, Generator  # noqa: E402

import pytest  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

import app.models  # noqa: F401, E402  — modellarni metadata'ga ro'yxatga oladi
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


def _sync_url(url: str) -> str:
    return url.replace("+asyncpg", "+psycopg2")


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> Generator[None, None, None]:
    """Test bazasini yaratadi va jadvallarni quradi.

    Sinxron engine ishlatiladi: sessiya darajasidagi async fixture
    pytest-asyncio da event loop bilan chalkashlik keltiradi.
    """
    admin_url = _sync_url(TEST_DB_URL).rsplit("/", 1)[0] + "/postgres"
    db_name = TEST_DB_URL.rsplit("/", 1)[1]

    admin = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        mavjud = conn.execute(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name}
        ).scalar()
        if not mavjud:
            conn.execute(sa.text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()

    engine = sa.create_engine(_sync_url(TEST_DB_URL))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()

    yield

    engine = sa.create_engine(_sync_url(TEST_DB_URL))
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Har bir test uchun tranzaksiya, oxirida rollback.

    Sessiya tashqi tranzaksiyaga ulangan ulanish ustida ishlaydi.
    `join_transaction_mode="create_savepoint"` tufayli ilova kodidagi
    `commit()` SAVEPOINT'ni bo'shatadi, tashqi tranzaksiya esa ochiq
    qoladi va oxirida bekor qilinadi — baza toza qoladi.
    """
    engine = create_async_engine(TEST_DB_URL)
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield db
    finally:
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """`get_session` test sessiyasiga qaratilgan HTTP klient."""

    async def override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    fastapi_app.dependency_overrides[get_session] = override
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def user_data() -> dict[str, str]:
    return {
        "email": "shifokor@example.uz",
        "username": "shifokor",
        "full_name": "Nodira Qodirova",
        "password": "Parol12345",
    }


@pytest.fixture
async def registered(client: AsyncClient, user_data: dict[str, str]) -> dict:
    """Ro'yxatdan o'tgan (lekin tasdiqlanmagan) foydalanuvchi."""
    r = await client.post("/auth/register", json=user_data)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
async def auth_headers(
    client: AsyncClient, registered: dict, user_data: dict[str, str]
) -> dict[str, str]:
    r = await client.post(
        "/auth/login",
        json={"login": user_data["email"], "password": user_data["password"]},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
