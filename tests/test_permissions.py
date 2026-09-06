"""Ruxsat qoidalari testlari."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.fixture
async def verified_headers(
    client: AsyncClient, registered: dict, user_data: dict[str, str]
) -> dict[str, str]:
    """Emaili tasdiqlangan foydalanuvchi sarlavhasi."""
    await client.get(f"/auth/verify-email?token={registered['verification_token']}")
    r = await client.post(
        "/auth/login",
        json={"login": user_data["email"], "password": user_data["password"]},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def boshqa_headers(client: AsyncClient) -> dict[str, str]:
    """Ikkinchi, tasdiqlangan foydalanuvchi."""
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
        "/posts",
        headers=verified_headers,
        json={"title": "Sinov posti", "content": "matn"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


class TestTasdiqlanmagan:
    """is_verified=false: ko'ra oladi va like bosa oladi, yoza olmaydi."""

    async def test_post_yoza_olmaydi(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        r = await client.post(
            "/posts", headers=auth_headers, json={"title": "Ruxsatsiz", "content": "m"}
        )

        assert r.status_code == 403
        assert r.json()["error"]["code"] == "email_not_verified"

    async def test_izoh_yoza_olmaydi(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        boshqa_headers: dict[str, str],
    ) -> None:
        p = await client.post(
            "/posts", headers=boshqa_headers, json={"title": "Boshqa post", "content": "m"}
        )

        r = await client.post(
            f"/posts/{p.json()['id']}/comments",
            headers=auth_headers,
            json={"content": "izoh"},
        )

        assert r.status_code == 403
        assert r.json()["error"]["code"] == "email_not_verified"

    async def test_postlarni_koqra_oladi(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        assert (await client.get("/posts", headers=auth_headers)).status_code == 200
        assert (await client.get("/all", headers=auth_headers)).status_code == 200

    async def test_like_bosa_oladi(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        boshqa_headers: dict[str, str],
    ) -> None:
        """Talab: tasdiqlanmagan foydalanuvchi like bosa oladi."""
        p = await client.post(
            "/posts", headers=boshqa_headers, json={"title": "Boshqa post", "content": "m"}
        )

        r = await client.post(f"/posts/{p.json()['id']}/like", headers=auth_headers)

        assert r.status_code == 201


class TestEgalik:
    """Har kim faqat o'z obyektini tahrirlaydi va o'chiradi."""

    async def test_begona_postni_tahrirlay_olmaydi(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        r = await client.patch(
            f"/posts/{post_id}", headers=boshqa_headers, json={"title": "Bosib olindi"}
        )

        assert r.status_code == 403
        assert r.json()["error"]["code"] == "forbidden"

    async def test_begona_postni_oqchira_olmaydi(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        r = await client.delete(f"/posts/{post_id}", headers=boshqa_headers)

        assert r.status_code == 403

    async def test_muallif_tahrirlaydi_va_oqchiradi(
        self, client: AsyncClient, post_id: str, verified_headers: dict[str, str]
    ) -> None:
        patch = await client.patch(
            f"/posts/{post_id}", headers=verified_headers, json={"title": "Yangilandi"}
        )
        assert patch.status_code == 200
        assert patch.json()["title"] == "Yangilandi"

        assert (
            await client.delete(f"/posts/{post_id}", headers=verified_headers)
        ).status_code == 204

    async def test_mavjud_boqlmagan_post(
        self, client: AsyncClient, verified_headers: dict[str, str]
    ) -> None:
        """404, 403 emas: avval mavjudlik, keyin egalik tekshiriladi."""
        r = await client.delete(f"/posts/{uuid.uuid4()}", headers=verified_headers)

        assert r.status_code == 404
        assert r.json()["error"]["code"] == "not_found"

    async def test_begona_izohni_oqchira_olmaydi(
        self,
        client: AsyncClient,
        post_id: str,
        verified_headers: dict[str, str],
        boshqa_headers: dict[str, str],
    ) -> None:
        """Post egasi ham begona izohni o'chira olmaydi."""
        izoh = await client.post(
            f"/posts/{post_id}/comments",
            headers=boshqa_headers,
            json={"content": "Boshqa odamning izohi"},
        )
        izoh_id = izoh.json()["id"]

        r = await client.delete(f"/posts/{post_id}/comments/{izoh_id}", headers=verified_headers)

        assert r.status_code == 403
        assert r.json()["error"]["code"] == "forbidden"

    async def test_izoh_muallifi_oqchiradi(
        self, client: AsyncClient, post_id: str, boshqa_headers: dict[str, str]
    ) -> None:
        izoh = await client.post(
            f"/posts/{post_id}/comments",
            headers=boshqa_headers,
            json={"content": "izoh"},
        )

        r = await client.delete(
            f"/posts/{post_id}/comments/{izoh.json()['id']}", headers=boshqa_headers
        )

        assert r.status_code == 204

    async def test_izoh_boshqa_postga_tegishli(
        self,
        client: AsyncClient,
        post_id: str,
        verified_headers: dict[str, str],
        boshqa_headers: dict[str, str],
    ) -> None:
        """Bir postning izohini boshqa post orqali o'chirib bo'lmaydi."""
        izoh = await client.post(
            f"/posts/{post_id}/comments", headers=boshqa_headers, json={"content": "izoh"}
        )
        ikkinchi = await client.post(
            "/posts", headers=verified_headers, json={"title": "Ikkinchi post", "content": "m"}
        )

        r = await client.delete(
            f"/posts/{ikkinchi.json()['id']}/comments/{izoh.json()['id']}",
            headers=boshqa_headers,
        )

        assert r.status_code == 404


class TestAvtorizatsiyasiz:
    async def test_yozish_amallari_yopiq(self, client: AsyncClient) -> None:
        post = await client.post("/posts", json={"title": "Anonim", "content": "m"})
        assert post.status_code == 401
        assert (await client.patch("/users/me", json={"full_name": "Hech Kim"})).status_code == 401

    async def test_oqqish_amallari_ochiq(self, client: AsyncClient) -> None:
        assert (await client.get("/posts")).status_code == 200
        assert (await client.get("/all")).status_code == 200
