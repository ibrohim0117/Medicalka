"""Modellarni bitta joyda yig'ish — Alembic autogenerate uchun kerak."""

from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.models.verification import VerificationToken, VerificationTokenType

__all__ = ["Comment", "Like", "Post", "User", "VerificationToken", "VerificationTokenType"]
