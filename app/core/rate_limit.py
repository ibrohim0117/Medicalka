"""Login urinishlarini cheklash — Redis hisoblagichlari orqali.

Redis mijozi har chaqiruvda ochilib yopiladi. Global mijoz saqlash
oqibati yomon: `redis.asyncio` mijozi o'zi yaratilgan event loop'ga
bog'lanadi va boshqa loop'da ishlatilsa yopilmagan soketlar qoladi
(testlarda har bir test o'z loop'ida ishlaydi). Login sekin amal
(argon2 ~33 ms), qo'shimcha ulanish sezilmaydi.

Redis ishlamay qolsa cheklov jimgina o'chadi: himoya vositasi asosiy
xizmatni to'xtatib qo'ymasligi kerak.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def redis_client() -> AsyncIterator[Redis]:
    client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


class LoginRateLimiter:
    """Kalit bo'yicha muvaffaqiyatsiz urinishlarni sanaydi.

    Kalit — IP va login juftligi. Faqat IP bo'lsa, umumiy NAT ortidagi
    barcha foydalanuvchilar bir-birini bloklardi; faqat login bo'lsa,
    hujumchi begona hisobni ataylab bloklab qo'yardi.
    """

    @property
    def yoqilgan(self) -> bool:
        return settings.LOGIN_RATE_LIMIT > 0

    @staticmethod
    def _kalit(ip: str, login: str) -> str:
        return f"login_attempts:{ip}:{login.lower()}"

    async def bloklanganmi(self, ip: str, login: str) -> bool:
        if not self.yoqilgan:
            return False
        try:
            async with redis_client() as r:
                soni = await r.get(self._kalit(ip, login))
        except Exception as exc:
            logger.warning("Rate limit tekshirib bo'lmadi: %s", exc)
            return False
        return soni is not None and int(soni) >= settings.LOGIN_RATE_LIMIT

    async def muvaffaqiyatsiz(self, ip: str, login: str) -> None:
        """Hisoblagichni oshiradi va muddat qo'yadi."""
        if not self.yoqilgan:
            return
        kalit = self._kalit(ip, login)
        try:
            async with redis_client() as r:
                soni = await r.incr(kalit)
                if soni == 1:
                    # Birinchi urinish — oyna boshlanadi.
                    await r.expire(kalit, settings.LOGIN_RATE_WINDOW_SECONDS)
                elif soni >= settings.LOGIN_RATE_LIMIT:
                    # Chegaraga yetdi — blok muddatiga uzaytiramiz.
                    await r.expire(kalit, settings.LOGIN_LOCKOUT_SECONDS)
        except Exception as exc:
            logger.warning("Rate limit hisoblagichi yangilanmadi: %s", exc)

    async def tozalash(self, ip: str, login: str) -> None:
        """Muvaffaqiyatli kirishdan keyin hisoblagich nolga tushadi."""
        if not self.yoqilgan:
            return
        try:
            async with redis_client() as r:
                await r.delete(self._kalit(ip, login))
        except Exception as exc:
            logger.warning("Rate limit hisoblagichi tozalanmadi: %s", exc)
