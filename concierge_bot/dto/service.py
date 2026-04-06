from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServiceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hotel_id: UUID
    name: str
    category: str
    description: str | None
    price: Decimal | None
    currency: str
    is_active: bool
    created_at: datetime
