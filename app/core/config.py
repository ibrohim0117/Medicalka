"""Ilova sozlamalari — .env dan o'qiladi.

DATABASE_URL va JWT_SECRET da standart qiymat yo'q: berilmasa yoki nomi
xato bo'lsa, ilova ishga tushishdayoq to'xtaydi.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Medicalka Social"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str
    SYNC_DATABASE_URL: str | None = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 30
    REFRESH_TOKEN_TTL_DAYS: int = 14
    EMAIL_VERIFY_TTL_HOURS: int = 24
    PASSWORD_RESET_TTL_HOURS: int = 2

    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # NoDecode: aks holda pydantic-settings "a,b" ni JSON deb ochishga urinadi.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @property
    def sync_database_url(self) -> str:
        """Celery va Alembic uchun sinxron driver (asyncpg -> psycopg2)."""
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
