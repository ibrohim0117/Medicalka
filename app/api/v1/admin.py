"""Admin ruchkalari — tozalash vazifalarini qo'lda ishga tushirish.

Barcha endpoint'lar `X-Admin-Token` sarlavhasini talab qiladi.
Vazifalar navbatga qo'yiladi va worker bajaradi — bu yerda sinxron
bajarilmaydi, chunki tozalash fon vazifasi bo'lishi shart.
"""

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import AdminOnly
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.rate_limit import redis_client
from app.schemas.admin import TaskAccepted, TaskStatus
from app.worker.celery_app import celery_app
from app.worker.tasks import (
    cleanup_expired_tokens,
    cleanup_old_posts,
    cleanup_unverified_users,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[AdminOnly])

_TASK_KEY = "admin_task:{}"


async def _eslab_qol(task_id: str, task_name: str) -> None:
    """Yuborilgan vazifa ID'sini Redis'da belgilab qo'yadi.

    Celery `AsyncResult` mavjud bo'lmagan ID uchun ham `PENDING`
    qaytaradi — u "hali bajarilmagan" va "bunday vazifa yo'q" ni
    ajratmaydi. Shuning uchun yuborganlarimizni o'zimiz eslab qolamiz.
    """
    try:
        async with redis_client() as r:
            await r.setex(_TASK_KEY.format(task_id), settings.ADMIN_TASK_TTL_SECONDS, task_name)
    except Exception:
        # Redis yiqilsa vazifa baribir yuborilgan — faqat holatini
        # "noma'lum" dan ajratib bo'lmaydi.
        pass


async def _bizniki(task_id: str) -> bool:
    try:
        async with redis_client() as r:
            return await r.get(_TASK_KEY.format(task_id)) is not None
    except Exception:
        # Redis yiqilsa tekshirib bo'lmaydi — javob berishni to'smaymiz.
        return True


@router.post(
    "/cleanup/unverified-users",
    response_model=TaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Tasdiqlanmagan hisoblarni tozalash",
)
async def run_cleanup_unverified_users(
    older_than_hours: int | None = Query(
        None,
        ge=1,
        description="Berilmasa UNVERIFIED_USER_TTL_HOURS ishlatiladi",
    ),
) -> TaskAccepted:
    """202 qaytadi: vazifa navbatga qo'yildi, natija darhol tayyor emas.

    Holatini `GET /admin/tasks/{task_id}` orqali bilish mumkin.
    """
    natija = cleanup_unverified_users.delay(older_than_hours=older_than_hours)
    await _eslab_qol(natija.id, cleanup_unverified_users.name)
    return TaskAccepted(task_id=natija.id, task=cleanup_unverified_users.name)


@router.post(
    "/cleanup/expired-tokens",
    response_model=TaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Eskirgan tasdiqlash tokenlarini tozalash",
)
async def run_cleanup_expired_tokens() -> TaskAccepted:
    natija = cleanup_expired_tokens.delay()
    await _eslab_qol(natija.id, cleanup_expired_tokens.name)
    return TaskAccepted(task_id=natija.id, task=cleanup_expired_tokens.name)


@router.post(
    "/cleanup/old-posts",
    response_model=TaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Eski postlarni tozalash",
)
async def run_cleanup_old_posts(
    older_than_days: int | None = Query(
        None, ge=1, description="Berilmasa POST_TTL_DAYS ishlatiladi"
    ),
) -> TaskAccepted:
    """`POST_TTL_DAYS=0` bo'lsa vazifa hech narsa o'chirmaydi."""
    natija = cleanup_old_posts.delay(older_than_days=older_than_days)
    await _eslab_qol(natija.id, cleanup_old_posts.name)
    return TaskAccepted(task_id=natija.id, task=cleanup_old_posts.name)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    summary="Vazifa holati",
)
async def get_task_status(task_id: str) -> TaskStatus:
    """Vazifa holati.

    Noma'lum ID uchun 404: yuborilgan vazifalar Redis'da belgilab
    qo'yiladi, shuning uchun "hali bajarilmagan" va "bunday vazifa yo'q"
    farqlanadi.
    """
    try:
        uuid.UUID(task_id)
    except ValueError as exc:
        raise NotFoundError("Vazifa topilmadi", code="task_not_found") from exc

    if not await _bizniki(task_id):
        raise NotFoundError("Vazifa topilmadi", code="task_not_found")

    natija = celery_app.AsyncResult(task_id)
    return TaskStatus(
        task_id=task_id,
        status=natija.state,
        result=natija.result if natija.successful() else None,
    )
