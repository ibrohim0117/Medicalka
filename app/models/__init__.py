"""Modellarni bitta joyda yig'ish — Alembic autogenerate uchun kerak."""

from app.models.user import User
from app.models.verification import VerificationToken, VerificationTokenType

__all__ = ["User", "VerificationToken", "VerificationTokenType"]
