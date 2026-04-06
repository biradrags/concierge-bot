from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HotelDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    admin_chat_id: int
    forum_chat_id: int | None
    bot_token: str
    max_bot_token: str | None
    system_prompt: str | None
    is_active: bool
    created_at: datetime
