"""FastAPI ilovasi — kirish nuqtasi."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import engine

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


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Biznes xatolarini HTTP javobga aylantiradi.

    Busiz servis tashlagan ConflictError ushlanmagan istisno bo'lib
    500 qaytarardi.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic xatolarini ham shu shaklga keltiradi: {"error": {...}}."""
    details = [
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Kiritilgan ma'lumotlar noto'g'ri",
                "details": details,
            }
        },
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
