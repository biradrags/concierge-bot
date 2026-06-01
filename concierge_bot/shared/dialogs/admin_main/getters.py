from typing import Any

from aiogram_dialog import DialogManager

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO


async def get_admin_dashboard(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    if hotel is None:
        return {"hotel_name": "—", "pending_count": 0}
    pending = await dao.booking.get_pending_by_hotel(hotel.id)
    return {"hotel_name": hotel.name, "pending_count": len(pending)}
