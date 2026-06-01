from typing import Any

from aiogram_dialog import DialogManager

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO


async def get_booking_stats(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    if hotel is None:
        return {"stats_text": "Нет данных"}
    stats = await dao.booking.get_stats_by_hotel(hotel.id)
    lines = [f"{k}: {v}" for k, v in sorted(stats.items())]
    body = "\n".join(lines) if lines else "Броней пока нет"
    return {"stats_text": body}
