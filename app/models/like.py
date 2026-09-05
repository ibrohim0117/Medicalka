"""Like modeli — jadval: `likes`.

Bitta jadval post va izohga xizmat qiladi: `post_id` yoki `comment_id`
dan faqat bittasi to'ldiriladi (CHECK cheklovi).

Cheklovlar:
    UNIQUE(user_id, post_id), UNIQUE(user_id, comment_id)
"""

# TODO: from app.db.base import Base
# class Like(Base): ...
