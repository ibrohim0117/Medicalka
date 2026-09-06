"""Admin ruchkalari uchun sxemalar."""

from typing import Any

from pydantic import BaseModel


class TaskAccepted(BaseModel):
    """Vazifa navbatga qo'yilgani haqida javob."""

    task_id: str
    task: str
    status: str = "queued"


class TaskStatus(BaseModel):
    """Vazifaning holati va natijasi."""

    task_id: str
    status: str
    result: Any | None = None
