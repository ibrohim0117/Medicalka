"""Post sxemalari."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.schemas.comment import CommentRead

TITLE_MIN, TITLE_MAX = 5, 255
CONTENT_MAX = 10_000


def _kes(value: str, min_length: int, nom: str) -> str:
    """Chetdagi bo'shliqlarni kesadi va uzunlikni QAYTA tekshiradi.

    Field(min_length=...) kesishdan oldin ishlaydi, shuning uchun "  abc  "
    besh belgi deb hisoblanib o'tib ketardi va uch belgi bo'lib saqlanardi.
    """
    cleaned = value.strip()
    if len(cleaned) < min_length:
        raise ValueError(f"{nom} kamida {min_length} belgi bo'lishi kerak")
    return cleaned


class PostCreate(BaseModel):
    """POST /posts kirishi."""

    title: str = Field(min_length=TITLE_MIN, max_length=TITLE_MAX)
    content: str = Field(min_length=1, max_length=CONTENT_MAX)

    @field_validator("title", mode="after")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return _kes(value, TITLE_MIN, "title")

    @field_validator("content", mode="after")
    @classmethod
    def clean_content(cls, value: str) -> str:
        return _kes(value, 1, "content")


class PostUpdate(BaseModel):
    """PATCH /posts/{id} kirishi — faqat yuborilgan maydonlar o'zgaradi."""

    title: str | None = Field(default=None, min_length=TITLE_MIN, max_length=TITLE_MAX)
    content: str | None = Field(default=None, min_length=1, max_length=CONTENT_MAX)

    @field_validator("title", mode="after")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        return _kes(value, TITLE_MIN, "title") if value is not None else None

    @field_validator("content", mode="after")
    @classmethod
    def clean_content(cls, value: str | None) -> str | None:
        return _kes(value, 1, "content") if value is not None else None


class PostRead(BaseModel):
    """Javoblardagi post."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class PostDetail(PostRead):
    """GET /posts/{id} — post va uning izohlari.

    `comments` to'ldirilishi uchun so'rovda `selectinload(Post.comments)`
    bo'lishi shart: modellarda `lazy="raise"` turibdi.
    """

    comments: list[CommentRead] = []


class PostFilters(BaseModel):
    """`GET /posts` filtrlari — qidiruv va sana oralig'i."""

    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_from", "date_to", mode="after")
    @classmethod
    def to_utc(cls, value: datetime | None) -> datetime | None:
        """Zonasiz sana UTC deb qabul qilinadi.

        `created_at` ustuni `timestamptz`. Zonasiz qiymat solishtirilsa,
        Postgres uni server zonasida talqin qiladi va natija server
        sozlamasiga bog'liq bo'lib qolardi.
        """
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @model_validator(mode="after")
    def check_range(self) -> "PostFilters":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from date_to dan keyin bo'lishi mumkin emas")
        return self


def post_filters(
    search: str | None = Query(
        None,
        min_length=1,
        max_length=255,
        description="title yoki content ichidan qidiradi (registrga sezgir emas)",
    ),
    date_from: datetime | None = Query(
        None, description="ISO 8601: 2026-09-06 yoki 2026-09-06T14:30:00Z"
    ),
    date_to: datetime | None = Query(
        None, description="ISO 8601. Shu lahzagacha, ya'ni 2026-09-06 = yarim tun"
    ),
) -> PostFilters:
    try:
        return PostFilters(search=search, date_from=date_from, date_to=date_to)
    except ValidationError as exc:
        # Dependency ichida tashlangan ValidationError'ni FastAPI o'zi
        # 422 ga aylantirmaydi — u ushlanmagan istisno bo'lib 500 berardi.
        raise RequestValidationError(exc.errors()) from exc


PostFiltersDep = Annotated[PostFilters, Depends(post_filters)]
