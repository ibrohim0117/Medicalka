"""Paginatsiya va umumiy javob shakllari."""

from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """`?page=1&size=20` — endpoint'larda dependency sifatida ishlatiladi."""

    page: int = Field(ge=1)
    size: int = Field(ge=1, le=settings.MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def pagination(
    page: int = Query(1, ge=1, description="Sahifa raqami, 1 dan boshlanadi"),
    size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Sahifadagi elementlar soni, {settings.MAX_PAGE_SIZE} gacha",
    ),
) -> PaginationParams:
    return PaginationParams(page=page, size=size)


PaginationDep = Annotated[PaginationParams, Depends(pagination)]


class Page(BaseModel, Generic[T]):
    """Sahifalangan javob. `total` — jami elementlar, `pages` — jami sahifalar."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if total else 0,
        )
