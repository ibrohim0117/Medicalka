"""Post so'rovlari.

Bu yerda nima bo'ladi:
    * `get_with_author` — muallif bilan birga (joinedload)
    * `list_posts` — lenta: paginatsiya, qidiruv, muallif bo'yicha filtr,
      hamda `viewer_id` berilsa EXISTS orqali "like bosganmi" ustuni
    * `adjust_counter` — `likes_count` / `comments_count` ni atomar o'zgartirish
"""

# TODO: from app.models.post import Post
