"""Foydalanuvchi modeli — jadval: `users`.

Ustunlar:
    id, email (unique), username (unique), hashed_password,
    full_name, bio, avatar_url, specialty, workplace,
    is_active, is_superuser, is_verified, last_login_at,
    created_at, updated_at

Bog'lanishlar:
    posts, comments, likes, verification_tokens
"""

# TODO: from app.db.base import Base, TimestampMixin
# class User(Base, TimestampMixin): ...
