"""Like sxemalari."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LikeRead(BaseModel):
    """POST /posts/{id}/like javobi."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
