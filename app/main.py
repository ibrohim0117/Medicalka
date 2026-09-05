"""FastAPI ilovasi — kirish nuqtasi.

Hozircha bu yerda faqat xizmat endpoint'lari bor: `/` va `/health`.
Qolgan qismlar tegishli modullar yozilgach ulanadi — pastdagi TODO'larga qarang.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from fastapi import FastAPI

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
    # TODO: await dispose_engine()  — app.db.session yozilgach
    logger.info("Medicalka Social to'xtatildi")


app = FastAPI(
    title="Medicalka Social",
    version=VERSION,
    description="Tibbiyot hamjamiyati uchun ijtimoiy tarmoq API.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# TODO: settings = get_settings()  — app.core.config
# TODO: CORSMiddleware ni ulash (settings.CORS_ORIGINS bo'sh bo'lmasa)
# TODO: register_exception_handlers(app)  — app.core.exceptions
# TODO: app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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
