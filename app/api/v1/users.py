"""`/users` endpoint'lari.

Endpoint'lar:
    GET    /users                       — ro'yxat + qidiruv
    PATCH  /users/me                    — o'z profilini tahrirlash
    DELETE /users/me                    — hisobni faolsizlantirish
    GET    /users/{user_id}             — profil
    GET    /users/by-username/{username}
    GET    /users/{user_id}/posts       — foydalanuvchining postlari
"""

# TODO: router = APIRouter(prefix="/users", tags=["users"])
