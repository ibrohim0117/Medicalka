# Medicalka Social

Tibbiyot hamjamiyati uchun ijtimoiy tarmoq API: foydalanuvchilar, publikatsiyalar,
izohlar, like'lar, JWT autentifikatsiya, email tasdiqlash va eskirgan ma'lumotlarni
fon vazifalari orqali tozalash.

**Stek:** Python 3.12 · FastAPI · PostgreSQL 16 · SQLAlchemy 2 (async) · Alembic ·
Celery + Redis · Docker

## Ishga tushirish

```bash
git clone <repo>
cd medicalka-social
cp .env.example .env
docker compose up --build
```

Beshta xizmat ko'tariladi: `db`, `redis`, `api`, `worker`, `beat`. `api` ishga
tushishda migratsiyalarni o'zi qo'llaydi — qo'shimcha buyruq kerak emas.

| Manzil | Nima |
|---|---|
| http://localhost:8000/docs | Swagger UI — endpointlarni shu yerdan sinash mumkin |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI spetsifikatsiyasi |
| http://localhost:8000/health | Tiriklik tekshiruvi |

`.env` da `JWT_SECRET` va `ADMIN_TOKEN` ni almashtiring:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Testlar

```bash
docker compose run --rm tests                    # pytest
docker compose run --rm tests ruff check .       # linter
docker compose run --rm tests ruff format .      # formatter
docker compose run --rm tests mypy app           # tiplar
```

Testlar alohida `medicalka_test` bazasida ishlaydi, asosiy bazaga tegmaydi.
`tests` xizmati `profiles: ["test"]` da, shuning uchun `docker compose up` uni
ko'tarmaydi.

Lokal ishlatish uchun:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d db
pytest
```

### pre-commit

```bash
pip install -e ".[dev]"
pre-commit install          # har commitda avtomatik ishlaydi
pre-commit run --all-files  # hammasini qo'lda tekshirish
```

Hooklar: ortiqcha bo'shliq, fayl oxiri, YAML/TOML sintaksisi, katta
fayllar, merge konflikt izlari, maxfiy kalitlar, `ruff` (`--fix` bilan),
`ruff format` va `mypy`.

### CI

`.github/workflows/ci.yml` uchta ishni bajaradi:

| Ish | Nima |
|---|---|
| `lint` | `ruff check`, `ruff format --check`, `mypy app` |
| `test` | Postgres xizmati ko'tariladi, `pytest -v` |
| `docker` | `runtime` va `dev` tasvirlari yig'iladi (kesh bilan) |

## Muhit o'zgaruvchilari

Barchasi `.env.example` da izohlar bilan. Eng muhimlari:

| O'zgaruvchi | Standart | Izoh |
|---|---|---|
| `DATABASE_URL` | — | **Majburiy.** Async ulanish qatori (asyncpg) |
| `SYNC_DATABASE_URL` | — | Ixtiyoriy. Berilmasa `DATABASE_URL` dan hosil qilinadi |
| `JWT_SECRET` | — | **Majburiy**, kamida 32 belgi |
| `ADMIN_TOKEN` | — | **Majburiy**, kamida 16 belgi. Admin ruchkalari uchun |
| `ACCESS_TOKEN_TTL_MINUTES` | 30 | |
| `REFRESH_TOKEN_TTL_DAYS` | 14 | |
| `EMAIL_VERIFY_TTL_HOURS` | 24 | Tasdiqlash havolasining umri |
| `UNVERIFIED_USER_TTL_HOURS` | 48 | Tasdiqlanmagan hisob shundan keyin o'chiriladi |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | 20 / 100 | |
| `DB_ECHO` | false | `true` — SQL so'rovlar logga chiqadi |

`DATABASE_URL` va `JWT_SECRET` da standart qiymat **ataylab yo'q**: nomi xato
yozilsa yoki berilmasa, ilova ishga tushishdayoq aniq xato bilan to'xtaydi.

## Endpointlar

Barchasi `/api/v1` prefiksi bilan.

### Autentifikatsiya

| Metod | Yo'l | Kim |
|---|---|---|
| POST | `/auth/register` | ochiq |
| POST | `/auth/login` | ochiq |
| POST | `/auth/refresh` | ochiq |
| GET | `/auth/verify-email?token=...` | ochiq |
| GET | `/auth/me` | token |

### Foydalanuvchilar

| Metod | Yo'l | Kim |
|---|---|---|
| PATCH | `/users/me` | token |

### Publikatsiyalar

| Metod | Yo'l | Kim |
|---|---|---|
| GET | `/posts` | ochiq |
| POST | `/posts` | tasdiqlangan |
| GET | `/posts/{post_id}` | ochiq |
| PATCH | `/posts/{post_id}` | muallif |
| DELETE | `/posts/{post_id}` | muallif |

`GET /posts` parametrlari: `page`, `page_size`, `search`, `date_from`, `date_to`.

### Izohlar va like'lar

| Metod | Yo'l | Kim |
|---|---|---|
| GET | `/posts/{post_id}/comments` | ochiq |
| POST | `/posts/{post_id}/comments` | tasdiqlangan |
| DELETE | `/posts/{post_id}/comments/{comment_id}` | izoh muallifi |
| POST | `/posts/{post_id}/like` | token (tasdiqlanmagan ham) |
| DELETE | `/posts/{post_id}/like` | token |

### Lenta va admin

| Metod | Yo'l | Kim |
|---|---|---|
| GET | `/all` | ochiq |
| POST | `/admin/cleanup/unverified-users` | `X-Admin-Token` |
| POST | `/admin/cleanup/expired-tokens` | `X-Admin-Token` |
| GET | `/admin/tasks/{task_id}` | `X-Admin-Token` |

## So'rov misollari

### Ro'yxatdan o'tish

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"shifokor@mail.uz","username":"shifokor",
       "full_name":"Nodira Qodirova","password":"Parol12345"}'
```

```json
{
  "user": {
    "id": "4e255a27-9f8b-4def-ad45-93bfe5ab2e76",
    "email": "shifokor@mail.uz",
    "username": "shifokor",
    "full_name": "Nodira Qodirova",
    "is_verified": false,
    "created_at": "2026-09-06T17:10:41.286587Z"
  },
  "verification_token": "IrA-tC4-xdmrAVwSlT-VumsU4zhArUJkbWfFNnC9oig"
}
```

SMTP yo'q, shuning uchun tasdiqlash tokeni javobda qaytadi.
`ENVIRONMENT=production` bo'lganda u `null` bo'ladi.

### Emailni tasdiqlash

```bash
curl "http://localhost:8000/api/v1/auth/verify-email?token=IrA-tC4-..."
```

### Kirish

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"shifokor@mail.uz","password":"Parol12345"}'
```

```json
{"access_token": "eyJhbGciOi...", "refresh_token": "eyJhbGciOi...", "token_type": "bearer"}
```

`login` maydoniga email ham, username ham yozish mumkin.

### Post yaratish

```bash
curl -X POST http://localhost:8000/api/v1/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Yurak sog'\''lig'\''i","content":"Kuniga 30 daqiqa yurish foydali"}'
```

### Qidiruv va filtr

```bash
curl "http://localhost:8000/api/v1/posts?search=yurak&date_from=2026-09-01&page=1&page_size=10"
```

```json
{
  "items": [...],
  "total": 8, "page": 1, "page_size": 10,
  "pages": 1, "has_next": false, "has_prev": false
}
```

### Umumiy lenta

```bash
curl "http://localhost:8000/api/v1/all?page_size=20"
```

```json
{
  "items": [
    {
      "id": "30735bb1-...",
      "username": "shifokor",
      "posts": [
        {
          "id": "19a9beeb-...",
          "title": "Yurak sog'lig'i",
          "content": "Kuniga 30 daqiqa yurish foydali",
          "likes": ["b4ba6e72-...", "2708cf70-..."]
        }
      ]
    }
  ],
  "total": 5, "page": 1, "page_size": 20, "pages": 1,
  "has_next": false, "has_prev": false
}
```

### Tozalashni qo'lda ishga tushirish

```bash
curl -X POST http://localhost:8000/api/v1/admin/cleanup/unverified-users \
  -H "X-Admin-Token: $ADMIN_TOKEN"
```

```json
{"task_id": "d956a060-...", "task": "app.worker.tasks.cleanup_unverified_users", "status": "queued"}
```

Endpoint ishni o'zi bajarmaydi — vazifani navbatga qo'yadi va **202** qaytaradi.
Natijani `GET /admin/tasks/{task_id}` orqali bilish mumkin.

### Xatolar

Barcha xatolar bir shaklda:

```json
{"error": {"code": "email_taken", "message": "Bu email allaqachon ro'yxatdan o'tgan"}}
```

Validatsiya xatosida qo'shimcha `details` bo'ladi:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Kiritilgan ma'lumotlar noto'g'ri",
    "details": [{"field": "username", "message": "String should match pattern '^[A-Za-z0-9_]+$'"}]
  }
}
```

## Loyiha tuzilmasi

```
app/
├── main.py            FastAPI ilovasi, router va handlerlarni ulash
├── core/
│   ├── config.py      Settings — barcha sozlamalar .env dan
│   ├── security.py    argon2 parol xeshi, JWT yaratish/tekshirish
│   └── exceptions.py  Biznes xatolari va HTTP handlerlari
├── db/
│   ├── base.py        DeclarativeBase, naming convention, TimestampMixin
│   ├── session.py     Async engine va get_session dependency
│   └── sync_session.py Sinxron engine — Celery worker uchun
├── models/            SQLAlchemy jadvallar
├── schemas/           Pydantic — kirish/chiqish shakllari va validatsiya
├── repositories/      Faqat SQL/ORM so'rovlari
├── services/          Biznes qoidalari va tranzaksiya chegaralari
├── api/
│   ├── deps.py        get_session, get_current_user, get_verified_user
│   └── v1/            Endpointlar
└── worker/
    ├── celery_app.py  Celery ilovasi va beat jadvali
    └── tasks.py       Tozalash vazifalari
```

Qatlamlar oqimi: **api → services → repositories → models**. Endpoint hech qachon
`select()` yozmaydi, servis HTTP haqida bilmaydi.

## Qabul qilingan qarorlar

**UUID birlamchi kalitlar, Python tomonda yaratiladi.** `default=uuid.uuid4` bilan
UUID `INSERT` ning o'ziga qo'shiladi — `RETURNING` kutilmaydi va kod Postgres
funksiyasiga bog'lanmaydi. Zaxira sifatida `server_default=gen_random_uuid()` ham
bor: ilovadan tashqarida qilingan `INSERT` ham ID oladi.

**argon2, bcrypt emas.** bcrypt faqat protsessorni band qiladi, argon2 xotirani ham
(64 MiB). Bu GPU'da parallel hujumni keskin qimmatlashtiradi. Yon foyda —
bcrypt'ning 72 baytlik chegarasi yo'q.

**Barcha `relationship`larda `lazy="raise"`.** Tasodifiy dangasa yuklash async'da
tushunarsiz `MissingGreenlet` xatosini beradi va N+1 so'rovlarga olib keladi.
`lazy="raise"` bunday kodni ishlab chiqishdayoq to'xtatadi va so'rovda
`selectinload` ni ochiq yozishga majbur qiladi.

**`/all` da `selectinload` zanjiri.** `selectinload(User.posts).selectinload(Post.likes)`
uch darajani uchta so'rovda oladi. 20 foydalanuvchi va 60 post bilan o'lchandi:
`options()` bilan **3 ta** so'rov, usiz **81 ta**.

`joinedload` bu yerda ishlatilmadi: u ikki darajali bog'lanishda dekart
ko'paytmasi beradi va har bir like uchun postning butun matnini qayta yuboradi.
O'lchov: 20 user / 60 post / 744 like da `joinedload` **919 kB**, `selectinload`
**124 kB**.

**Ruxsat qoidalari ikki joyda.** "Kimsan?" — `deps.py` dagi dependency
(`CurrentUser`, `VerifiedUser`), endpoint imzosida ko'rinadi. "Bu seniki mi?" —
servis qatlamida, obyekt yuklangan joyda. Post baribir yuklanadi (404 uchun), ya'ni
egalik tekshiruvi qo'shimcha so'rov talab qilmaydi va HTTP'siz chaqiruvlarda ham
amal qiladi.

**"O'z postiga like yo'q" — servisda, "bir marta" — bazada.** Farqi poyga
holatida: takroriy like'da tekshiruv va `INSERT` orasida oyna bor, shuning uchun
`UNIQUE(user_id, post_id)` majburiy. 30 ta parallel so'rov bilan sinaldi — bittasi
201, o'ttiz to'qqiztasi 409. O'z postiga like'da esa oyna yo'q: `posts.author_id`
o'zgarmaydi.

**Tozalash worker orqali, sinxron ruchka emas.** Admin endpointi `.delay()` bilan
navbatga qo'yadi va **202** qaytaradi. Beat jadvali: tasdiqlanmagan hisoblar har
kuni 03:00 da, eskirgan tokenlar har soat.

**Testlar tranzaksiya bilan izolyatsiyalanadi.** Har bir test ochiq tranzaksiya
ichida ishlaydi va oxirida rollback qilinadi. Jadvallar qayta yaratilmaydi —
24 ta test 2 soniyada o'tadi.

**Dockerfile uch bosqichli.** `builder` bog'liqliklarni yig'adi, `runtime` da
kompilyator qolmaydi (291 MB), `dev` esa testlar uchun (442 MB). Bog'liqliklar kod
COPY qilinishidan oldin o'rnatiladi — kod o'zgarganda `pip install` qatlami
keshdan olinadi.

## Migratsiyalar

```bash
docker compose exec api alembic revision --autogenerate -m "izoh"
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

Alembic async engine bilan ishlaydi va `DATABASE_URL` ni `app.core.config` dan
oladi, shuning uchun `alembic.ini` da `sqlalchemy.url` yozilmagan.

## Nima qilinmagan

- Haqiqiy SMTP — tasdiqlash tokeni javobda qaytadi
- Login'da rate limiting
- Refresh tokenlarni bekor qilish ro'yxati (`jti` bor, denylist yo'q)
