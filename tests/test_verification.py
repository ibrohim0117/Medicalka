"""Email tasdiqlash va eskirgan hisoblarni tozalash testlari."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import User, VerificationToken
from app.services.auth import AuthService


class TestVerifyEmail:
    async def test_tasdiqlash(self, client: AsyncClient, registered: dict) -> None:
        assert registered["user"]["is_verified"] is False

        r = await client.get(f"/auth/verify-email?token={registered['verification_token']}")

        assert r.status_code == 200, r.text
        assert r.json()["is_verified"] is True

    async def test_token_ishlatilgan_deb_belgilanadi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        await client.get(f"/auth/verify-email?token={registered['verification_token']}")

        token = (await session.execute(select(VerificationToken))).scalar_one()
        assert token.used_at is not None

    async def test_qayta_ishlatib_boqlmaydi(self, client: AsyncClient, registered: dict) -> None:
        tok = registered["verification_token"]
        await client.get(f"/auth/verify-email?token={tok}")

        r = await client.get(f"/auth/verify-email?token={tok}")

        assert r.status_code == 400
        assert r.json()["error"]["code"] == "token_used"

    async def test_soxta_token(self, client: AsyncClient) -> None:
        r = await client.get(f"/auth/verify-email?token={'x' * 43}")

        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_token"

    async def test_muddati_oqtgan_token(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        await session.execute(
            update(VerificationToken).values(expires_at=datetime.now(UTC) - timedelta(hours=1))
        )

        r = await client.get(f"/auth/verify-email?token={registered['verification_token']}")

        assert r.status_code == 400
        assert r.json()["error"]["code"] == "token_expired"

    async def test_muddati_oqtganda_tasdiqlanmaydi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        await session.execute(
            update(VerificationToken).values(expires_at=datetime.now(UTC) - timedelta(hours=1))
        )
        await client.get(f"/auth/verify-email?token={registered['verification_token']}")

        user = (await session.execute(select(User))).scalar_one()
        assert user.is_verified is False

    async def test_juda_qisqa_token(self, client: AsyncClient) -> None:
        r = await client.get("/auth/verify-email?token=qisqa")

        assert r.status_code == 422


class TestEskirganHisoblarniTozalash:
    """Vazifa mantig'i — `AuthService` emas, `cleanup_unverified_users` ichidagi
    shartlar bilan bir xil so'rov."""

    @staticmethod
    async def _tozalash(session: AsyncSession, soat: int = 48) -> int:
        """Vazifadagi shartning aynan o'zi, async sessiyada."""
        from sqlalchemy import delete

        chegara = datetime.now(UTC) - timedelta(hours=soat)
        natija = await session.execute(
            delete(User).where(User.is_verified.is_(False), User.created_at < chegara)
        )
        return natija.rowcount or 0

    async def test_eski_tasdiqlanmagan_oqchadi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        await session.execute(
            update(User).values(created_at=datetime.now(UTC) - timedelta(hours=72))
        )

        soni = await self._tozalash(session)

        assert soni == 1
        qolgan = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        assert qolgan == 0

    async def test_yangi_tasdiqlanmagan_qoladi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        """2 soatlik hisob 48 soatlik chegaradan o'tmaydi."""
        soni = await self._tozalash(session)

        assert soni == 0

    async def test_eski_tasdiqlangan_qoladi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        await client.get(f"/auth/verify-email?token={registered['verification_token']}")
        await session.execute(
            update(User).values(created_at=datetime.now(UTC) - timedelta(hours=99))
        )

        soni = await self._tozalash(session)

        assert soni == 0

    async def test_chegara(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        """47 soat — qoladi, 49 soat — o'chadi."""
        await session.execute(
            update(User).values(created_at=datetime.now(UTC) - timedelta(hours=47))
        )
        assert await self._tozalash(session) == 0

        await session.execute(
            update(User).values(created_at=datetime.now(UTC) - timedelta(hours=49))
        )
        assert await self._tozalash(session) == 1

    async def test_tokenlar_ham_oqchadi(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        """ON DELETE CASCADE — alohida so'rov kerak emas."""
        await session.execute(
            update(User).values(created_at=datetime.now(UTC) - timedelta(hours=72))
        )

        await self._tozalash(session)

        tokenlar = (
            await session.execute(select(func.count()).select_from(VerificationToken))
        ).scalar_one()
        assert tokenlar == 0


class TestQaytaYuborish:
    async def test_har_bir_royxatdan_oqtish_yangi_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        """Ikkita foydalanuvchi — ikkita alohida token."""
        for i in (1, 2):
            await client.post(
                "/auth/register",
                json={
                    "email": f"user{i}@example.uz",
                    "username": f"user{i}",
                    "full_name": "Test Nom",
                    "password": "Parol12345",
                },
            )

        tokenlar = (await session.execute(select(VerificationToken.token))).scalars().all()
        assert len(tokenlar) == 2
        assert len(set(tokenlar)) == 2

    async def test_boshqa_odamning_tokeni_bilan(
        self, client: AsyncClient, session: AsyncSession, registered: dict
    ) -> None:
        """Token faqat o'z egasini tasdiqlaydi."""
        r = await client.post(
            "/auth/register",
            json={
                "email": "ikkinchi@example.uz",
                "username": "ikkinchi",
                "full_name": "Ikkinchi Odam",
                "password": "Parol12345",
            },
        )

        await client.get(f"/auth/verify-email?token={r.json()['verification_token']}")

        birinchi = (
            await session.execute(
                select(User).where(User.id == uuid.UUID(registered["user"]["id"]))
            )
        ).scalar_one()
        assert birinchi.is_verified is False


class TestServisDarajasida:
    async def test_verify_email_notoqri_token(self, session: AsyncSession) -> None:
        """Servis HTTP'siz ham ishlaydi."""
        from app.core.exceptions import InvalidTokenError

        try:
            await AuthService(session).verify_email("mavjud-boqlmagan-token")
        except InvalidTokenError as exc:
            assert exc.status_code == 400
        else:
            raise AssertionError("istisno kutilgan edi")


class TestQaytaSoqrash:
    """POST /auth/resend-verification — sovish davri bilan."""

    @staticmethod
    async def _headers(client: AsyncClient, user_data: dict[str, str]) -> dict[str, str]:
        r = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": user_data["password"]},
        )
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    @staticmethod
    async def _sovishni_oqtkaz(session: AsyncSession) -> None:
        """Oxirgi tokenni sovish davridan oldinroq qilib qo'yadi."""
        oldin = datetime.now(UTC) - timedelta(
            seconds=settings.RESEND_VERIFICATION_COOLDOWN_SECONDS + 60
        )
        await session.execute(update(VerificationToken).values(created_at=oldin))

    async def test_sovish_davri_ichida_rad_etiladi(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        h = await self._headers(client, user_data)

        r = await client.post("/auth/resend-verification", headers=h)

        assert r.status_code == 429
        assert r.json()["error"]["code"] == "resend_too_soon"

    async def test_sovish_davridan_keyin_yangi_token(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        h = await self._headers(client, user_data)
        await self._sovishni_oqtkaz(session)

        r = await client.post("/auth/resend-verification", headers=h)

        assert r.status_code == 200, r.text
        assert r.json()["verification_token"] != registered["verification_token"]

    async def test_eski_token_bekor_qilinadi(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        h = await self._headers(client, user_data)
        await self._sovishni_oqtkaz(session)
        await client.post("/auth/resend-verification", headers=h)

        r = await client.get(f"/auth/verify-email?token={registered['verification_token']}")

        assert r.status_code == 400
        assert r.json()["error"]["code"] == "token_used"

    async def test_yangi_token_ishlaydi(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        h = await self._headers(client, user_data)
        await self._sovishni_oqtkaz(session)
        yangi = (await client.post("/auth/resend-verification", headers=h)).json()

        r = await client.get(f"/auth/verify-email?token={yangi['verification_token']}")

        assert r.status_code == 200
        assert r.json()["is_verified"] is True

    async def test_muddati_oqtgan_tokendan_keyin(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        """Asosiy stsenariy: havola eskirdi, foydalanuvchi yangisini oladi."""
        h = await self._headers(client, user_data)
        await session.execute(
            update(VerificationToken).values(
                expires_at=datetime.now(UTC) - timedelta(hours=1),
                created_at=datetime.now(UTC) - timedelta(hours=25),
            )
        )
        eski = await client.get(f"/auth/verify-email?token={registered['verification_token']}")
        assert eski.json()["error"]["code"] == "token_expired"

        yangi = (await client.post("/auth/resend-verification", headers=h)).json()
        r = await client.get(f"/auth/verify-email?token={yangi['verification_token']}")

        assert r.status_code == 200
        assert r.json()["is_verified"] is True

    async def test_tasdiqlangandan_keyin(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        await client.get(f"/auth/verify-email?token={registered['verification_token']}")
        h = await self._headers(client, user_data)
        await self._sovishni_oqtkaz(session)

        r = await client.post("/auth/resend-verification", headers=h)

        assert r.status_code == 409
        assert r.json()["error"]["code"] == "already_verified"

    async def test_tokensiz(self, client: AsyncClient) -> None:
        r = await client.post("/auth/resend-verification")

        assert r.status_code == 401

    async def test_faqat_bitta_faol_token_qoladi(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        h = await self._headers(client, user_data)
        for _ in range(3):
            await self._sovishni_oqtkaz(session)
            await client.post("/auth/resend-verification", headers=h)

        faol = (
            await session.execute(
                select(func.count())
                .select_from(VerificationToken)
                .where(VerificationToken.used_at.is_(None))
            )
        ).scalar_one()
        assert faol == 1
