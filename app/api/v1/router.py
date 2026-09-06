"""v1 router'larini bitta joyga yig'ish."""

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()
api_router.include_router(auth.router)
