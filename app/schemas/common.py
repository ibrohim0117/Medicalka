"""Paginatsiya va umumiy javob shakllari."""

from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """`?page=1&page_size=20` — endpoint'larda dependency sifatida ishlatiladi."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=settings.MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination(
    page: int = Query(1, ge=1, description="Sahifa raqami, 1 dan boshlanadi"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Sahifadagi elementlar soni, {settings.MAX_PAGE_SIZE} gacha",
    ),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


PaginationDep = Annotated[PaginationParams, Depends(pagination)]


class Page(BaseModel, Generic[T]):
    """Sahifalangan javob.

    `has_next` / `has_prev` mijoz tomonda `page < pages` deb hisoblanishi
    mumkin edi, lekin chegaralarda xato qilish oson (`total=0` da `pages=0`
    va `page=1`). Serverda bir marta hisoblanadi.
    """

    items: list[T]
    total: int = Field(description="Jami elementlar soni")
    page: int = Field(description="Joriy sahifa")
    page_size: int = Field(description="Sahifadagi elementlar soni")
    pages: int = Field(description="Jami sahifalar soni")
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        pages = ceil(total / params.page_size) if total else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )
