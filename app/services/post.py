"""Post biznes-mantig'i: yaratish, tahrirlash, o'chirish, ro'yxat."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Post, User
from app.repositories.post import PostRepository
from app.schemas.common import PaginationParams
from app.schemas.post import PostCreate, PostFilters, PostUpdate


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.posts = PostRepository(session)

    async def get(self, post_id: uuid.UUID) -> Post:
        post = await self.posts.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post topilmadi")
        return post

    async def get_detail(self, post_id: uuid.UUID) -> Post:
        """Post va izohlari birga."""
        post = await self.posts.get_with_comments(post_id)
        if post is None:
            raise NotFoundError("Post topilmadi")
        return post

    async def list_posts(
        self, params: PaginationParams, filters: PostFilters
    ) -> tuple[Sequence[Post], int]:
        return await self.posts.list_posts(
            offset=params.offset,
            limit=params.page_size,
            search=filters.search,
            date_from=filters.date_from,
            date_to=filters.date_to,
        )

    async def create(self, user: User, data: PostCreate) -> Post:
        post = await self.posts.create(author_id=user.id, title=data.title, content=data.content)
        await self.session.commit()
        return post

    async def update(self, post_id: uuid.UUID, user: User, data: PostUpdate) -> Post:
        post = await self._own_post(post_id, user)
        # exclude_unset: yuborilmagan maydonga tegilmaydi (PATCH semantikasi).
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(post, key, value)
        await self.session.commit()
        await self.session.refresh(post)  # updated_at server tomonda yangilanadi
        return post

    async def delete(self, post_id: uuid.UUID, user: User) -> None:
        post = await self._own_post(post_id, user)
        await self.posts.delete(post)
        await self.session.commit()

    async def _own_post(self, post_id: uuid.UUID, user: User) -> Post:
        """Post mavjudligini va egasi shu foydalanuvchi ekanini tekshiradi.

        Egalik tekshiruvi shu yerda, endpoint'da emas: post baribir
        yuklanadi, ya'ni tekshiruv qo'shimcha so'rov talab qilmaydi. Va
        qoida HTTP'siz chaqiruvlarda ham amal qiladi.
        """
        post = await self.get(post_id)
        if post.author_id != user.id:
            raise ForbiddenError("Bu post sizga tegishli emas")
        return post
