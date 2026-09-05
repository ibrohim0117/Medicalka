"""Ilova sozlamalari (Pydantic Settings).

Bu yerda nima bo'ladi:
    * `class Settings(BaseSettings)` — `.env` dan o'qiydigan barcha sozlamalar:
      APP_NAME, ENVIRONMENT, DEBUG, API_V1_PREFIX,
      SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
      POSTGRES_* , REDIS_URL, CELERY_*, CORS_ORIGINS
    * `async_database_url` / `sync_database_url` — hisoblanadigan xossalar
    * `get_settings()` — `@lru_cache` bilan keshlangan yagona nusxa
"""

# TODO: from pydantic_settings import BaseSettings, SettingsConfigDict

# class Settings(BaseSettings): ...
# settings = get_settings()
