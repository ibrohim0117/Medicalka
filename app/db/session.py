"""Asinxron engine va sessiya fabrikasi (FastAPI uchun).

Bu yerda nima bo'ladi:
    * `engine = create_async_engine(settings.async_database_url, ...)`
    * `AsyncSessionLocal = async_sessionmaker(bind=engine, ...)`
    * `async def get_session()` — FastAPI dependency, so'rov davomida
      bitta sessiya beradi va xatolikda rollback qiladi
"""

# TODO: from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# TODO: from app.core.config import settings
