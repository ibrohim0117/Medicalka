# syntax=docker/dockerfile:1
#
# Medicalka Social — ikki bosqichli konteyner tasviri.
#
#   builder  — kompilyator va -dev sarlavhalar bilan bog'liqliklarni yig'adi
#   runtime  — faqat ishlash uchun kerak bo'lgani; kompilyator qolmaydi
#
# Yig'ish:   docker build -t medicalka-social .
# Ishlatish: docker run --rm -p 8000:8000 --env-file .env medicalka-social

# 1. BUILDER
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# `build-essential` va `libpq-dev` — faqat yig'ish uchun; runtime'ga o'tmaydi.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Bog'liqliklar alohida virtual muhitga — keyin uni butunligicha ko'chiramiz.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Qatlam 1: faqat bog'liqliklar
# Avval yolg'iz `pyproject.toml` ko'chiriladi va undan bog'liqliklar
# ro'yxati ajratib olinadi. Kod o'zgarganda bu qatlam keshdan olinadi —
# `pip install` qaytadan ishlamaydi.
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -c "\
import tomllib, pathlib;\
deps = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['dependencies'];\
pathlib.Path('/tmp/requirements.txt').write_text('\n'.join(deps))" \
 && pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt

# Qatlam 2: loyiha kodi
# `README.md` ham kerak: pyproject.toml da `readme = "README.md"` yozilgan.
# `--no-deps` — bog'liqliklar yuqorida o'rnatilgan, qayta tekshirilmaydi.
COPY README.md ./
COPY app ./app
RUN pip install --no-deps .

# 2. RUNTIME
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Medicalka Social" \
      org.opencontainers.image.description="Tibbiyot hamjamiyati uchun ijtimoiy tarmoq API" \
      org.opencontainers.image.source="https://github.com/ibrohim/medicalka-social"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# `libpq5` — psycopg2 uchun ishlash vaqtidagi kutubxona (dev sarlavhalarsiz).
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 appuser \
 # Celery beat jadval faylini shu yerga yozadi. Katalog tasvirda appuser
 # nomiga yaratilgani muhim: compose unga nomli volume ulaganda Docker
 # egalikni shu katalogdan nusxalaydi, aks holda volume root'niki bo'lib
 # qoladi va beat yoza olmaydi.
 && mkdir -p /var/lib/celery \
 && chown appuser:appuser /var/lib/celery

COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv/app

# `app/` paketi allaqachon /opt/venv ichiga o'rnatilgan, shuning uchun bu
# yerga faqat migratsiyalar ko'chiriladi — kodning ikki nusxasi bo'lmaydi.
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations ./migrations

USER appuser

EXPOSE 8000

# curl o'rniga python — qo'shimcha paket o'rnatish shart emas.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
