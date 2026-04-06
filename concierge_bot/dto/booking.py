from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from concierge_bot.dto.guest import GuestDTO
from concierge_bot.dto.service import ServiceDTO


class BookingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    guest_id: UUID
    service_id: UUID
    status: str
    notes: str | None
    created_at: datetime
    service: ServiceDTO | None = None
    guest: GuestDTO | None = None
