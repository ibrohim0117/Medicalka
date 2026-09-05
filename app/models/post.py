"""Post modeli — jadval: `posts`.

Ustunlar:
    id, author_id (FK -> users.id, CASCADE), title, body, image_url,
    is_published, likes_count, comments_count, created_at, updated_at

Eslatma: `likes_count` / `comments_count` — denormallashtirilgan
hisoblagichlar, lentada har safar COUNT(*) qilmaslik uchun.
"""

# TODO: from app.db.base import Base, TimestampMixin
# class Post(Base, TimestampMixin): ...
