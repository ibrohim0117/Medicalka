"""Fon vazifalari — tozalash va hisoblagichlarni tiklash.

Barchasi sinxron sessiya (`app.db.sync_session.session_scope`) bilan ishlaydi.

Vazifalar:
    * `cleanup_expired_tokens` — muddati o'tgan tasdiqlash token'larini o'chirish
    * `purge_inactive_users` — 30 kundan beri faolsiz hisoblarni o'chirish
    * `resync_counters` — `likes_count` / `comments_count` ni haqiqiy
      qiymatlarga tenglashtirish (drift tuzatish)
    * `send_verification_email` — tasdiqlash xatini yuborish (SMTP)
"""

# TODO: from app.worker.celery_app import celery_app
# TODO: from app.db.sync_session import session_scope
