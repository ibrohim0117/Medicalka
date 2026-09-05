"""Umumiy xato klasslari va FastAPI handler'lari.

Bu yerda nima bo'ladi:
    * `AppError` — barcha biznes xatolarining ota klassi
      (`status_code`, `code`, `message`, `details`)
    * Vorislari: `NotFoundError`, `AlreadyExistsError`, `ValidationError`,
      `AuthenticationError`, `PermissionDeniedError`, `InactiveUserError`
    * Handler'lar: AppError, HTTPException, RequestValidationError,
      IntegrityError va ushlanmagan Exception uchun
    * `register_exception_handlers(app)` — main.py dan chaqiriladi
"""

# TODO: from fastapi import FastAPI, status
# TODO: class AppError(Exception): ...
