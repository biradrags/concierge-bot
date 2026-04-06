from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GuestDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    telegram_user_id: int
    hotel_id: UUID
    name: str | None
    language_code: str
    forum_topic_id: int | None
    created_at: datetime
