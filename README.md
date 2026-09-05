# Medicalka Social

Tibbiyot hamjamiyati uchun ijtimoiy tarmoq API — **FastAPI + PostgreSQL + Celery**.

> Hozircha bu **skelet**: papka tuzilmasi, konfiguratsiya fayllari va har bir
> modulda nima bo'lishini tushuntiruvchi izohlar tayyor. Kod yozilmagan.

## Tuzilma

```
app/
├── main.py           # FastAPI ilovasi, router'larni ulash
├── core/             # config, security (JWT/parol), exceptions
├── db/               # Base, async sessiya, Celery uchun sync sessiya
├── models/           # SQLAlchemy jadvallar
├── schemas/          # Pydantic — kirish/chiqish shakllari
├── repositories/     # faqat SQL/ORM so'rovlari
├── services/         # biznes-mantiq va qoidalar
├── api/              # deps.py + v1/ endpoint'lar
└── worker/           # Celery ilovasi va fon vazifalari
```

Qatlamlar oqimi: `api → services → repositories → models`.
Endpoint hech qachon to'g'ridan-to'g'ri ORM bilan ishlamaydi.

## Ishga tushirish

```bash
cp .env.example .env          # SECRET_KEY ni almashtiring
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Tiriklik: http://localhost:8000/health

Xizmatlar: `api`, `worker` (Celery), `beat` (jadval), `db` (Postgres 16),
`redis`.

## Lokal ishlab chiqish

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head
uvicorn app.main:app --reload
pytest
```

## Migratsiyalar

```bash
alembic revision --autogenerate -m "izoh"
alembic upgrade head
alembic downgrade -1
```

`migrations/env.py` sozlamalarni `app.core.config` dan oladi, shuning uchun
`alembic.ini` da `sqlalchemy.url` yozilmagan.

## Rejalashtirilgan endpoint'lar

| Metod | Yo'l | Tavsif |
|---|---|---|
| POST | `/api/v1/auth/register` | Ro'yxatdan o'tish |
| POST | `/api/v1/auth/login` | Kirish (email yoki username) |
| POST | `/api/v1/auth/refresh` | Access token'ni yangilash |
| POST | `/api/v1/auth/verify-email` | Emailni tasdiqlash |
| GET | `/api/v1/auth/me` | Joriy foydalanuvchi |
| GET/PATCH | `/api/v1/users/...` | Profillar |
| CRUD | `/api/v1/posts` | Postlar |
| CRUD | `/api/v1/posts/{id}/comments` | Izohlar |
| POST | `/api/v1/posts/{id}/like` | Like (toggle) |
| GET | `/api/v1/feed/all` | Umumiy lenta |
