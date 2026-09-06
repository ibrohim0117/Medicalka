"""Biznes xatolari. HTTP kodi shu yerda, servis FastAPI'ni bilmaydi."""


class AppError(Exception):
    """Barcha biznes xatolarining ota klassi."""

    status_code = 400
    code = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


class ConflictError(AppError):
    """Resurs allaqachon mavjud — masalan email band."""

    status_code = 409
    code = "conflict"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthError(AppError):
    """Login yoki parol noto'g'ri, token yaroqsiz."""

    status_code = 401
    code = "unauthorized"


class InvalidTokenError(AppError):
    """Tasdiqlash tokeni yaroqsiz, ishlatilgan yoki muddati o'tgan."""

    status_code = 400
    code = "invalid_token"
