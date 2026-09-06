"""Biznes xatolari va ularni HTTP javobga aylantiruvchi handler'lar.

Xato klasslari FastAPI'ni import qilmaydi — ular faqat `status_code` va
`code` ni olib yuradi. Shuning uchun servis qatlamini HTTP'siz (test,
Celery, CLI) ishlatish mumkin.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Barcha biznes xatolarining ota klassi."""

    status_code = 400
    code = "app_error"

    def __init__(
        self, message: str, *, code: str | None = None, status_code: int | None = None
    ) -> None:
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        super().__init__(message)


class ConflictError(AppError):
    """Resurs allaqachon mavjud — masalan email band."""

    status_code = 409
    code = "conflict"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthError(AppError):
    """Kim ekaningiz noma'lum: token yo'q, yaroqsiz yoki muddati o'tgan."""

    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    """Kim ekaningiz ma'lum, lekin bu amalga ruxsatingiz yo'q.

    401 dan farqi: qayta kirish yordam bermaydi.
    """

    status_code = 403
    code = "forbidden"


class InvalidTokenError(AppError):
    """Tasdiqlash tokeni yaroqsiz, ishlatilgan yoki muddati o'tgan."""

    status_code = 400
    code = "invalid_token"


def _javob(status_code: int, code: str, message: str, details: object = None) -> JSONResponse:
    xato: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        xato["details"] = details
    return JSONResponse(status_code=status_code, content={"error": xato})


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    """Biznes xatolari. Busiz ular ushlanmagan istisno bo'lib 500 qaytardi."""
    assert isinstance(exc, AppError)
    return _javob(exc.status_code, exc.code, exc.message)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    """Pydantic xatolari — qaysi maydon va nima uchun."""
    assert isinstance(exc, RequestValidationError)
    details = [
        {"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return _javob(422, "validation_error", "Kiritilgan ma'lumotlar noto'g'ri", details)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    """FastAPI/Starlette o'z xatolari: noma'lum yo'l 404, noto'g'ri metod 405.

    Ular standart holda `{"detail": "..."}` qaytaradi — boshqa shaklda.
    Bu yerda ularni ham `{"error": {...}}` ga keltiramiz.
    """
    assert isinstance(exc, StarletteHTTPException)
    return _javob(exc.status_code, f"http_{exc.status_code}", str(exc.detail))


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    """Kutilmagan xatolar uchun oxirgi to'siq.

    Stek izi logga yoziladi, mijozga esa umumiy xabar ketadi: ichki yo'llar,
    SQL matni va kutubxona versiyalari tashqariga chiqmasin.
    """
    logger.exception("Ushlanmagan xatolik", exc_info=exc)
    return _javob(500, "internal_error", "Serverda ichki xatolik yuz berdi")


def register_exception_handlers(app: FastAPI) -> None:
    """main.py dan chaqiriladi — barcha handler'larni ilovaga ulaydi."""
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unhandled)
