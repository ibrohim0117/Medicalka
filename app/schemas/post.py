"""Post sxemalari."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
