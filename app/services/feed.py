"""`/all` lentasi biznes-mantig'i."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.schemas.common import PaginationParams
from app.schemas.feed import FeedPost, FeedUser


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def list_all(self, params: PaginationParams) -> tuple[list[FeedUser], int]:
        users, total = await self.users.list_with_posts_and_likes(
            offset=params.offset, limit=params.page_size
        )
        # Saralash Python tomonda: ma'lumot allaqachon yuklangan, qo'shimcha
        # so'rov kerak emas. Bir foydalanuvchining postlari kamdan-kam
        # yuzdan oshadi, xotirada saralash tekin.
        items = [
            FeedUser(
                id=user.id,
                username=user.username,
                posts=[
                    FeedPost(
                        id=post.id,
                        title=post.title,
                        content=post.content,
                        likes=[like.user_id for like in post.likes],
                    )
                    for post in sorted(user.posts, key=lambda p: p.created_at, reverse=True)
                ],
            )
            for user in users
        ]
        return items, total
