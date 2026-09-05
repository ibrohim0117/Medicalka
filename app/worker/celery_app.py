"""Celery ilovasi va beat jadvali.

Bu yerda nima bo'ladi:
    * `celery_app = Celery("medicalka", broker=..., backend=...)`
    * `celery_app.conf.update(...)` — serializer, timezone, time limit
    * `celery_app.conf.beat_schedule` — davriy vazifalar:
        - cleanup_expired_tokens  (har soatda)
        - purge_inactive_users    (kuniga bir marta)
        - resync_counters         (kuniga bir marta)

Ishga tushirish:
    celery -A app.worker.celery_app:celery_app worker --loglevel=info
    celery -A app.worker.celery_app:celery_app beat   --loglevel=info
"""

# TODO: from celery import Celery
# TODO: from app.core.config import settings
