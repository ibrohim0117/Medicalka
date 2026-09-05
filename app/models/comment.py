"""Izoh modeli — jadval: `comments`.

Ustunlar:
    id, post_id (FK), author_id (FK), parent_id (FK -> comments.id, javob
    uchun), body, likes_count, created_at, updated_at
"""

# TODO: from app.db.base import Base, TimestampMixin
# class Comment(Base, TimestampMixin): ...
