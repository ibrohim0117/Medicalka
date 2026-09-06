"""`/auth` endpoint'lari."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.schemas.user import RegisterResponse, Token, UserCreate, UserLogin, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ro'yxatdan o'tish",
)
async def register(data: UserCreate, session: SessionDep) -> RegisterResponse:
    """Yangi hisob yaratadi.

    Foydalanuvchi `is_verified = false` bilan yaratiladi va unga bir
    martalik tasdiqlash tokeni beriladi (muddati `EMAIL_VERIFY_TTL_HOURS`).
    """
    user, raw_token = await AuthService(session).register(data)
    return RegisterResponse(
        user=UserRead.model_validate(user),
        verification_token=None if settings.ENVIRONMENT == "production" else raw_token,
    )


@router.post("/login", response_model=Token, summary="Tizimga kirish")
async def login(data: UserLogin, session: SessionDep) -> Token:
    """Access token qaytaradi.

    `login` maydoniga email ham, username ham yozish mumkin. Noto'g'ri
    login va noto'g'ri parol bir xil xato beradi — qaysi hisob mavjudligi
    oshkor bo'lmasin.
    """
    return Token(access_token=await AuthService(session).login(data))


@router.get("/me", response_model=UserRead, summary="Joriy foydalanuvchi")
async def me(user: CurrentUser) -> UserRead:
    """`Authorization: Bearer <token>` sarlavhasidagi tokenga tegishli hisob."""
    return UserRead.model_validate(user)
