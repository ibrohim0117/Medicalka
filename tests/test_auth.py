"""Autentifikatsiya oqimi testlari.

Nimalar tekshiriladi:
    * register — muvaffaqiyatli yaratish, takroriy email/username, zaif parol
    * login — email va username bilan, noto'g'ri parol
    * /auth/me — token talab qilinishi, yaroqsiz token
    * refresh — yangi token, access token'ni refresh sifatida rad etish
    * verify-email — tasdiqlash, token'ni qayta ishlatib bo'lmasligi
    * change-password
"""

# TODO: from httpx import AsyncClient
