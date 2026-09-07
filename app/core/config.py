"""Ilova sozlamalari — .env dan o'qiladi.

DATABASE_URL va JWT_SECRET da standart qiymat yo'q: berilmasa yoki nomi
xato bo'lsa, ilova ishga tushishdayoq to'xtaydi.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# .env.example bilan birga keladigan qiymatlar. Ular 32/16 belgilik
# chegaradan o'tadi, shuning uchun uzunlik tekshiruvi ularni ushlamaydi —
# production uchun alohida rad etiladi.
PLACEHOLDER_SECRETS = frozenset(
    {
        "dev-uchun-vaqtinchalik-kalit-almashtiring",
        "change-me-admin-token-min-16-belgi",
    }
)


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
    # Admin ruchkalari uchun umumiy sir. To'liq admin autentifikatsiyasi
    # o'rniga — texnik tugma, X-Admin-Token sarlavhasida yuboriladi.
    ADMIN_TOKEN: str = Field(min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 30
    REFRESH_TOKEN_TTL_DAYS: int = 14
    EMAIL_VERIFY_TTL_HOURS: int = 24
    PASSWORD_RESET_TTL_HOURS: int = 2
    # Tasdiqlash xatini qayta so'rash orasidagi eng kam vaqt.
    RESEND_VERIFICATION_COOLDOWN_SECONDS: int = 120
    # Tasdiqlanmagan hisob shu muddatdan keyin o'chiriladi.
    UNVERIFIED_USER_TTL_HOURS: int = 48
    # Postlarni avtomatik o'chirish. 0 — o'chirilmaydi.
    POST_TTL_DAYS: int = 0

    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    # Testlarda `True`: vazifa navbatsiz, o'sha yerda bajariladi.
    CELERY_TASK_ALWAYS_EAGER: bool = False
    # Admin yuborgan vazifa ID'lari shu muddat davomida eslab qolinadi.
    ADMIN_TASK_TTL_SECONDS: int = 3600

    # NoDecode: aks holda pydantic-settings "a,b" ni JSON deb ochishga urinadi.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    # SMTP. SMTP_HOST bo'sh bo'lsa xat yuborilmaydi, faqat logga yoziladi.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@medicalka.uz"
    SMTP_STARTTLS: bool = True
    # Xatdagi havola shu manzildan quriladi.
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Login'ga hujumdan himoya. 0 — cheklov o'chirilgan.
    LOGIN_RATE_LIMIT: int = 10
    LOGIN_RATE_WINDOW_SECONDS: int = 300
    LOGIN_LOCKOUT_SECONDS: int = 900

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @model_validator(mode="after")
    def namunaviy_sirlarni_rad_etish(self) -> "Settings":
        """Production'da .env.example dagi qiymatlar bilan ishga tushmaydi.

        Namunaviy qiymatlar uzunlik chegarasidan o'tadi (aks holda yangi
        klon `cp .env.example .env` dan keyin ko'tarilmasdi), shuning uchun
        ularni alohida ushlash kerak.
        """
        if self.ENVIRONMENT != "production":
            return self
        band = [
            nom
            for nom in ("JWT_SECRET", "ADMIN_TOKEN")
            if getattr(self, nom) in PLACEHOLDER_SECRETS
        ]
        if band:
            raise ValueError(
                f"{', '.join(band)} .env.example dagi namunaviy qiymatda qolgan. "
                "Production uchun yangisini yarating: "
                'python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        return self

    @property
    def sync_database_url(self) -> str:
        """Celery va Alembic uchun sinxron driver (asyncpg -> psycopg2)."""
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
