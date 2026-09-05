"""JWT yaratish/tekshirish va parol xeshlash.

Bu yerda nima bo'ladi:
    * `hash_password(password)` / `verify_password(password, hash)` — bcrypt
    * `create_access_token(subject)` / `create_refresh_token(subject)`
    * `decode_token(token, expected_type)` — imzo, muddat va tur tekshiruvi
    * `generate_verification_token()` / `hash_verification_token(token)`
      — email tasdiqlash uchun bir martalik token (bazada faqat xeshi saqlanadi)
"""

# TODO: import bcrypt, jwt
# TODO: from app.core.config import settings
