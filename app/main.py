"""FastAPI ilovasi — kirish nuqtasi."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import AsyncSessionLocal, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _app_version() -> str:
    """Versiyani `pyproject.toml` dan oladi — bir joyda saqlanishi uchun."""
    try:
        return package_version("medicalka-social")
    except PackageNotFoundError:
        # Paket o'rnatilmagan holda (masalan konteynerda `pip install -e` siz)
        # ishga tushirilsa, ilova yiqilmasligi kerak.
        return "0.0.0+unknown"


VERSION = _app_version()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Ishga tushish va to'xtash paytidagi amallar."""
    logger.info("Medicalka Social %s ishga tushdi", VERSION)
    yield
    await engine.dispose()
    logger.info("Medicalka Social to'xtatildi")


app = FastAPI(
    title="Medicalka Social",
    version=VERSION,
    description="Tibbiyot hamjamiyati uchun ijtimoiy tarmoq API.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# TODO: CORSMiddleware — frontend ulangach, settings.CORS_ORIGINS bo'yicha.


@app.get(
    "/",
    tags=["service"],
    summary="Xizmat haqida",
    response_description="Xizmat nomi, versiyasi va foydali havolalar",
)
async def root() -> dict[str, str]:
    """Xizmatning qisqacha ta'rifi va hujjatlarga havolalar."""
    return {
        "name": "Medicalka Social",
        "version": VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["service"],
    summary="Tiriklik tekshiruvi",
    response_description="Xizmat javob berayotgan bo'lsa doim `ok`",
)
async def health() -> dict[str, str]:
    """Yengil tekshiruv — tashqi bog'liqliklarga (baza, Redis) tegmaydi.

    Docker `HEALTHCHECK` va load balancer shu endpoint'ni so'raydi, shuning
    uchun u tez va nojoiz xatosiz bo'lishi kerak.

    Bazaga ulanishni tekshiradigan `/health/db` keyinroq, `app.db.session`
    yozilgandan so'ng qo'shiladi.
    """
    return {"status": "ok", "version": VERSION}


@app.get(
    "/health/db",
    tags=["service"],
    summary="Bazaga ulanish tekshiruvi",
    response_description="Baza javob bersa `ok`, aks holda 503",
)
async def health_db() -> JSONResponse:
    """Bazaga ulanishni tekshiradi.

    `/health` dan alohida: uni load balancer har necha soniyada so'raydi
    va u tashqi xizmatlarga bog'liq bo'lmasligi kerak. Bu esa nosozlikni
    tashxislash uchun — qo'lda yoki monitoring tomonidan so'raladi.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Bazaga ulanib bo'lmadi: %s", exc)
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "down"})
    return JSONResponse(content={"status": "ok", "database": "up"})


register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
