"""Admin ruchkalari — tozalash vazifalarini qo'lda ishga tushirish.

Barcha endpoint'lar `X-Admin-Token` sarlavhasini talab qiladi.
Vazifalar navbatga qo'yiladi va worker bajaradi — bu yerda sinxron
bajarilmaydi, chunki tozalash fon vazifasi bo'lishi shart.
"""

from fastapi import APIRouter, Query, status

from app.api.deps import AdminOnly
from app.schemas.admin import TaskAccepted, TaskStatus
from app.worker.celery_app import celery_app
from app.worker.tasks import (
    cleanup_expired_tokens,
    cleanup_old_posts,
    cleanup_unverified_users,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[AdminOnly])


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
    return TaskAccepted(task_id=natija.id, task=cleanup_unverified_users.name)


@router.post(
    "/cleanup/expired-tokens",
    response_model=TaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Eskirgan tasdiqlash tokenlarini tozalash",
)
async def run_cleanup_expired_tokens() -> TaskAccepted:
    natija = cleanup_expired_tokens.delay()
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
    return TaskAccepted(task_id=natija.id, task=cleanup_old_posts.name)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatus,
    summary="Vazifa holati",
)
async def get_task_status(task_id: str) -> TaskStatus:
    """PENDING — hali bajarilmagan yoki bunday vazifa umuman yo'q.

    Celery ikkalasini ajratmaydi: natijalar bazasida yozuv bo'lmasa,
    holat PENDING deb qaytadi.
    """
    natija = celery_app.AsyncResult(task_id)
    return TaskStatus(
        task_id=task_id,
        status=natija.state,
        result=natija.result if natija.successful() else None,
    )
