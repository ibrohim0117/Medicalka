"""Izoh sxemalari."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

CONTENT_MAX = 2_000


class CommentCreate(BaseModel):
    """POST /posts/{id}/comments kirishi."""

    content: str = Field(min_length=1, max_length=CONTENT_MAX)

    @field_validator("content", mode="after")
    @classmethod
    def clean_content(cls, value: str) -> str:
        """Kesishdan keyin qayta tekshiriladi: Field(min_length) kesishdan
        oldin ishlaydi va "   " ni uch belgi deb hisoblardi."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("izoh bo'sh bo'lishi mumkin emas")
        return cleaned


class CommentRead(BaseModel):
    """Javoblardagi izoh. Izohda updated_at yo'q — model shunday."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    created_at: datetime
