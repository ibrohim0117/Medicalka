"""`/all` — foydalanuvchilar, postlari va like'lari."""

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.common import Page, PaginationDep
from app.schemas.feed import FeedUser
from app.services.feed import FeedService

router = APIRouter(tags=["feed"])


@router.get("/all", response_model=Page[FeedUser], summary="Umumiy lenta")
async def list_all(session: SessionDep, params: PaginationDep) -> Page[FeedUser]:
    """Foydalanuvchilar, ularning postlari va har bir postga like bosganlar.

    Paginatsiya foydalanuvchilar bo'yicha: bir sahifada `page_size` ta
    foydalanuvchi va ularning barcha postlari.

    Avtorizatsiya talab qilinmaydi.
    """
    items, total = await FeedService(session).list_all(params)
    return Page.create(items, total, params)
