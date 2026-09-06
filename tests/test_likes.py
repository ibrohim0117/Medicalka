"""Like qoidalari testlari."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Like


@pytest.fixture
async def verified_headers(
    client: AsyncClient, registered: dict, user_data: dict[str, str]
) -> dict[str, str]:
    await client.get(f"/auth/verify-email?token={registered['verification_token']}")
    r = await client.post(
        "/auth/login",
        json={"login": user_data["email"], "password": user_data["password"]},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def boshqa_headers(client: AsyncClient) -> dict[str, str]:
    r = await client.post(
        "/auth/register",
        json={
            "email": "boshqa@example.uz",
            "username": "boshqa",
            "full_name": "Boshqa Odam",
            "password": "Parol12345",
        },
    )
    await client.get(f"/auth/verify-email?token={r.json()['verification_token']}")
    login = await client.post(
        "/auth/login", json={"login": "boshqa@example.uz", "password": "Parol12345"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def post_id(client: AsyncClient, verified_headers: dict[str, str]) -> str:
    r = await client.post(
        "/posts", headers=verified_headers, json={"title": "Sinov posti", "content": "m"}
    )
    return r.json()["id"]


class TestLike:
    async def test_begona_postga_like(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        r = await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        assert r.status_code == 201, r.text
        assert r.json()["post_id"] == post_id

    async def test_oqz_postiga_like_boqlmaydi(
        self, client: AsyncClient, post_id: str, verified_headers: dict[str, str]
    ) -> None:
        r = await client.post(f"/posts/{post_id}/like", headers=verified_headers)

        assert r.status_code == 403
        assert r.json()["error"]["code"] == "self_like"

    async def test_oqz_postiga_like_bazaga_yozilmaydi(
        self,
        client: AsyncClient,
        session: AsyncSession,
        post_id: str,
        verified_headers: dict[str, str],
    ) -> None:
        await client.post(f"/posts/{post_id}/like", headers=verified_headers)

        soni = (await session.execute(select(func.count()).select_from(Like))).scalar_one()
        assert soni == 0

    async def test_ikki_marta_like_boqlmaydi(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        birinchi = await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)
        assert birinchi.status_code == 201

        ikkinchi = await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        assert ikkinchi.status_code == 409
        assert ikkinchi.json()["error"]["code"] == "already_liked"

    async def test_takroriy_urinishdan_keyin_bitta_qator(
        self,
        client: AsyncClient,
        session: AsyncSession,
        post_id: str,
        boshqa_headers: dict[str, str],
    ) -> None:
        for _ in range(3):
            await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        soni = (await session.execute(select(func.count()).select_from(Like))).scalar_one()
        assert soni == 1

    async def test_mavjud_boqlmagan_post(
        self, client: AsyncClient, boshqa_headers: dict[str, str]
    ) -> None:
        r = await client.post(f"/posts/{uuid.uuid4()}/like", headers=boshqa_headers)

        assert r.status_code == 404

    async def test_tokensiz(self, client: AsyncClient, post_id: str) -> None:
        r = await client.post(f"/posts/{post_id}/like")

        assert r.status_code == 401


class TestUnlike:
    async def test_olib_tashlash(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        r = await client.delete(f"/posts/{post_id}/like", headers=boshqa_headers)

        assert r.status_code == 204

    async def test_bosmagan_odam_olib_tashlay_olmaydi(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        r = await client.delete(f"/posts/{post_id}/like", headers=boshqa_headers)

        assert r.status_code == 404
        assert r.json()["error"]["code"] == "like_not_found"

    async def test_qayta_bosish_mumkin(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        """like → unlike → like ketma-ketligi ishlashi kerak."""
        await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)
        await client.delete(f"/posts/{post_id}/like", headers=boshqa_headers)

        r = await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        assert r.status_code == 201


class TestLentadaLike:
    async def test_all_da_like_uuid_lari(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        me = await client.get("/auth/me", headers=boshqa_headers)
        bosgan_id = me.json()["id"]
        await client.post(f"/posts/{post_id}/like", headers=boshqa_headers)

        lenta = await client.get("/all")

        postlar = [p for u in lenta.json()["items"] for p in u["posts"]]
        sinov = next(p for p in postlar if p["id"] == post_id)
        assert sinov["likes"] == [bosgan_id]
