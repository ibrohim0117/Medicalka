"""Autentifikatsiya testlari."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models import User, VerificationToken


class TestRegister:
    async def test_muvaffaqiyatli_royxatdan_otish(
        self, client: AsyncClient, user_data: dict[str, str]
    ) -> None:
        r = await client.post("/auth/register", json=user_data)

        assert r.status_code == 201, r.text
        user = r.json()["user"]
        assert user["email"] == user_data["email"]
        assert user["username"] == user_data["username"]
        assert user["full_name"] == user_data["full_name"]
        # Yangi hisob har doim tasdiqlanmagan holatda yaratiladi.
        assert user["is_verified"] is False
        assert user["id"]
        assert user["created_at"]

    async def test_javobda_parol_yoq(self, client: AsyncClient, user_data: dict[str, str]) -> None:
        """Parol ham, uning xeshi ham javobga tushmasligi kerak."""
        r = await client.post("/auth/register", json=user_data)

        matn = r.text
        assert "password" not in matn
        assert "argon2" not in matn

    async def test_bazada_parol_xesh_sifatida(
        self, client: AsyncClient, session: AsyncSession, user_data: dict[str, str]
    ) -> None:
        await client.post("/auth/register", json=user_data)

        user = (
            await session.execute(select(User).where(User.email == user_data["email"]))
        ).scalar_one()
        assert user.password_hash != user_data["password"]
        assert user.password_hash.startswith("$argon2id$")

    async def test_tasdiqlash_tokeni_yaratiladi(
        self, client: AsyncClient, session: AsyncSession, user_data: dict[str, str]
    ) -> None:
        r = await client.post("/auth/register", json=user_data)
        ochiq_token = r.json()["verification_token"]

        token = (await session.execute(select(VerificationToken))).scalar_one()
        assert token.used_at is None
        # Bazada ochiq token emas, uning sha256 xeshi saqlanadi.
        assert token.token != ochiq_token
        assert len(token.token) == 64

    async def test_registr_normallashtiriladi(
        self, client: AsyncClient, user_data: dict[str, str]
    ) -> None:
        """Ali va ali bitta hisob bo'lsin — unique indeks registrga sezgir."""
        r = await client.post(
            "/auth/register",
            json={**user_data, "email": "SHIFOKOR@Example.UZ", "username": "Shifokor"},
        )

        assert r.status_code == 201
        assert r.json()["user"]["email"] == "shifokor@example.uz"
        assert r.json()["user"]["username"] == "shifokor"

    async def test_takroriy_email(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """Email band — username boshqa bo'lsa ham rad etiladi."""
        r = await client.post("/auth/register", json={**user_data, "username": "boshqa_nom"})

        assert r.status_code == 409
        assert r.json()["error"]["code"] == "email_taken"

    async def test_takroriy_username(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        r = await client.post("/auth/register", json={**user_data, "email": "boshqa@example.uz"})

        assert r.status_code == 409
        assert r.json()["error"]["code"] == "username_taken"

    async def test_takroriy_email_boshqa_registrda(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """SHIFOKOR@... va shifokor@... bitta hisob deb hisoblanadi."""
        r = await client.post(
            "/auth/register",
            json={
                **user_data,
                "email": user_data["email"].upper(),
                "username": "boshqa_nom",
            },
        )

        assert r.status_code == 409
        assert r.json()["error"]["code"] == "email_taken"

    async def test_takroriy_username_boshqa_registrda(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        r = await client.post(
            "/auth/register",
            json={
                **user_data,
                "email": "boshqa@example.uz",
                "username": user_data["username"].upper(),
            },
        )

        assert r.status_code == 409
        assert r.json()["error"]["code"] == "username_taken"

    async def test_dublikatdan_keyin_ikkinchi_yozuv_yoq(
        self,
        client: AsyncClient,
        session: AsyncSession,
        registered: dict,
        user_data: dict[str, str],
    ) -> None:
        """Rad etilgan urinish bazada iz qoldirmasligi kerak."""
        await client.post("/auth/register", json={**user_data, "username": "boshqa"})

        soni = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        assert soni == 1


class TestLogin:
    async def test_email_bilan(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        r = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": user_data["password"]},
        )

        assert r.status_code == 200, r.text
        javob = r.json()
        assert javob["token_type"] == "bearer"
        assert javob["access_token"]
        assert javob["refresh_token"]

    async def test_username_bilan(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """`login` maydoni email ham, username ham qabul qiladi."""
        r = await client.post(
            "/auth/login",
            json={"login": user_data["username"], "password": user_data["password"]},
        )

        assert r.status_code == 200, r.text
        assert r.json()["access_token"]

    async def test_registr_ahamiyatsiz(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        r = await client.post(
            "/auth/login",
            json={
                "login": user_data["email"].upper(),
                "password": user_data["password"],
            },
        )

        assert r.status_code == 200

    async def test_token_toqri_foydalanuvchini_koqrsatadi(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """Token ichidagi `sub` ro'yxatdan o'tgan hisobning ID'si bo'lsin."""
        r = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": user_data["password"]},
        )
        token = r.json()["access_token"]

        me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["id"] == registered["user"]["id"]

    async def test_tasdiqlanmagan_ham_kira_oladi(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """Talab: tasdiqlanmagan foydalanuvchi login qila oladi."""
        assert registered["user"]["is_verified"] is False

        r = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": user_data["password"]},
        )

        assert r.status_code == 200

    async def test_notoqri_parol(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        r = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": "NotoQriParol9"},
        )

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "invalid_credentials"

    async def test_mavjud_boqlmagan_hisob(self, client: AsyncClient) -> None:
        """Xato xabari noto'g'ri parol bilan bir xil — hisob bor-yo'qligi
        oshkor bo'lmasin."""
        r = await client.post(
            "/auth/login", json={"login": "yoq@example.uz", "password": "Parol12345"}
        )

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "invalid_credentials"


class TestHimoyalanganEndpoint:
    async def test_toqri_token(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        r = await client.get("/auth/me", headers=auth_headers)

        assert r.status_code == 200, r.text
        assert r.json()["username"] == "shifokor"

    async def test_token_yoq(self, client: AsyncClient) -> None:
        r = await client.get("/auth/me")

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "not_authenticated"

    async def test_axlat_token(self, client: AsyncClient) -> None:
        r = await client.get("/auth/me", headers={"Authorization": "Bearer bu.token.emas"})

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "invalid_token"

    async def test_boshqa_kalit_bilan_imzolangan(self, client: AsyncClient) -> None:
        """Imzo tekshiruvi: to'g'ri shakldagi, lekin begona kalit bilan
        imzolangan token o'tmasligi kerak."""
        soxta = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "type": "access",
                "jti": uuid.uuid4().hex,
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "butunlay-boshqa-kalit-uzun-bolsin",
            algorithm="HS256",
        )

        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {soxta}"})

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "invalid_token"

    async def test_muddati_oqtgan_token(self, client: AsyncClient, registered: dict) -> None:
        eskirgan = jwt.encode(
            {
                "sub": registered["user"]["id"],
                "type": "access",
                "jti": uuid.uuid4().hex,
                "exp": datetime.now(UTC) - timedelta(minutes=1),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {eskirgan}"})

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "token_expired"

    async def test_refresh_token_access_oqrnida(
        self, client: AsyncClient, registered: dict, user_data: dict[str, str]
    ) -> None:
        """Uzoq umrli refresh token qisqa umrli access o'rnini bosmasin."""
        login = await client.post(
            "/auth/login",
            json={"login": user_data["email"], "password": user_data["password"]},
        )
        refresh = login.json()["refresh_token"]

        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {refresh}"})

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "invalid_token"

    async def test_oqchirilgan_foydalanuvchi_tokeni(
        self, client: AsyncClient, registered: dict
    ) -> None:
        """Token amal qilsa ham, hisob yo'q bo'lsa kirish yopiladi."""
        token = create_access_token(str(uuid.uuid4()))

        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 401
        assert r.json()["error"]["code"] == "user_not_found"


class TestHealth:
    async def test_health(self, client: AsyncClient) -> None:
        r = await client.get("http://test/health")

        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_health_db(self, client: AsyncClient) -> None:
        """Baza ishlab turganda `up` qaytadi."""
        r = await client.get("http://test/health/db")

        assert r.status_code == 200
        assert r.json() == {"status": "ok", "database": "up"}
