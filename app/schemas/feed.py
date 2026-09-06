"""`/all` lentasi uchun sxemalar."""

import uuid

from pydantic import BaseModel


class FeedPost(BaseModel):
    """Lentadagi post. `likes` — like bosgan foydalanuvchilar UUID ro'yxati."""

    id: uuid.UUID
    title: str
    content: str
    likes: list[uuid.UUID]


class FeedUser(BaseModel):
    """Foydalanuvchi va uning postlari."""

    id: uuid.UUID
    username: str
    posts: list[FeedPost]
