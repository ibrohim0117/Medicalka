"""Deklarativ Base va umumiy ustunlar.

Bu yerda nima bo'ladi:
    * `NAMING_CONVENTION` — indeks/cheklov nomlari uchun yagona shablon
    * `class Base(DeclarativeBase)` — `metadata` va avtomatik `__tablename__`
    * `class TimestampMixin` — `created_at` / `updated_at`

Eslatma: modellar bu yerda import qilinmaydi (aylanma import bo'lmasligi
uchun) — ular `app/models/__init__.py` da yig'iladi.
"""

# TODO: from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# class Base(DeclarativeBase): ...
