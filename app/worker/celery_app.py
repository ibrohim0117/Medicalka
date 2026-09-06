"""Celery ilovasi va beat jadvali.

Ishga tushirish:
    celery -A app.worker.celery_app:celery_app worker --loglevel=info
    celery -A app.worker.celery_app:celery_app beat   --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "medicalka",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Vazifalar shu moduldan qidiriladi, aks holda worker ularni ko'rmaydi.
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Tashkent",
    enable_utc=True,
    # acks_late: vazifa bajarilib bo'lgach tasdiqlanadi. Worker o'rtada
    # o'lsa, vazifa yo'qolmaydi va boshqa worker uni qayta oladi.
    task_acks_late=True,
    # Har bir worker bir vaqtda bitta vazifa oladi — uzoq vazifalar
    # navbatda turib qolmasin.
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    # Broker javob bermasa uzoq kutmasin — `.delay()` chaqiruvi HTTP
    # so'rovni bloklab qo'ymasligi kerak.
    broker_transport_options={"socket_timeout": 3, "socket_connect_timeout": 3},
    broker_connection_max_retries=1,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)

celery_app.conf.beat_schedule = {
    # Tasdiqlanmagan hisoblar — kuniga bir marta, tunda.
    "cleanup-unverified-users": {
        "task": "app.worker.tasks.cleanup_unverified_users",
        "schedule": crontab(hour=3, minute=0),
    },
    # Eskirgan tokenlar — har soatda, arzon amal.
    "cleanup-expired-tokens": {
        "task": "app.worker.tasks.cleanup_expired_tokens",
        "schedule": crontab(minute=30),
    },
    # Eski postlar — POST_TTL_DAYS=0 bo'lsa vazifa o'zi hech narsa qilmaydi.
    "cleanup-old-posts": {
        "task": "app.worker.tasks.cleanup_old_posts",
        "schedule": crontab(hour=4, minute=0),
    },
}
