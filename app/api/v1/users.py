"""`/users` endpoint'lari."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserRead, summary="Profilni tahrirlash")
async def update_me(data: UserUpdate, user: CurrentUser, session: SessionDep) -> UserRead:
    """Joriy foydalanuvchining `full_name` va `username` maydonlari.

    Faqat so'rovda yuborilgan maydonlar o'zgaradi. Email va parol bu yerda
    tahrirlanmaydi — ular alohida endpoint talab qiladi.
    """
    updated = await UserService(session).update_profile(user, data)
    return UserRead.model_validate(updated)
