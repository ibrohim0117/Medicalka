"""`/auth` endpoint'lari."""

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.schemas.user import (
    RefreshRequest,
    RegisterResponse,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
)
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
    access, refresh = await AuthService(session).login(data)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token, summary="Tokenni yangilash")
async def refresh(data: RefreshRequest, session: SessionDep) -> Token:
    """Refresh token evaziga yangi access va refresh juftligi.

    Access token qisqa umrli (30 daqiqa) — parolni qayta so'ramasdan
    yangilash uchun shu endpoint ishlatiladi.
    """
    access, refresh_token = await AuthService(session).refresh(data.refresh_token)
    return Token(access_token=access, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead, summary="Joriy foydalanuvchi")
async def me(user: CurrentUser) -> UserRead:
    """`Authorization: Bearer <token>` sarlavhasidagi tokenga tegishli hisob."""
    return UserRead.model_validate(user)


@router.get("/verify-email", response_model=UserRead, summary="Emailni tasdiqlash")
async def verify_email(
    session: SessionDep,
    token: str = Query(min_length=16, max_length=256, description="Emaildagi token"),
) -> UserRead:
    """Tasdiqlash havolasi.

    Token topilmasa, allaqachon ishlatilgan bo'lsa yoki muddati o'tgan
    bo'lsa 400 qaytadi — uchalasi uchun alohida `code`. Muvaffaqiyatli
    bo'lsa `is_verified` `true` ga o'tadi.
    """
    return UserRead.model_validate(await AuthService(session).verify_email(token))
