from typing import Any
from uuid import UUID

from aiogram_dialog import DialogManager

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO


async def get_pending_bookings(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    if hotel is None:
        return {"bookings": []}
    rows = await dao.booking.get_pending_by_hotel(hotel.id)
    items = []
    for b in rows:
        svc_name = b.service.name if b.service else "?"
        items.append(
            {
                "id": str(b.id),
                "label": f"{svc_name} · {b.id}",
            },
        )
    return {"bookings": items}


async def get_booking_detail(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    raw = dialog_manager.dialog_data.get("booking_id")
    if not raw:
        return {"detail_text": "Не выбрано"}
    bid = UUID(raw)
    b = await dao.booking.get_by_id(bid)
    if b is None:
        return {"detail_text": "Бронь не найдена"}
    svc_name = b.service.name if b.service else "?"
    guest_label = str(b.guest.telegram_user_id) if b.guest else "?"
    text = (
        f"<b>Бронь</b>\n"
        f"Услуга: {svc_name}\n"
        f"Гость: {guest_label}\n"
        f"Статус: {b.status}\n"
        f"ID: <code>{b.id}</code>"
    )
    if b.notes:
        text += f"\nЗаметки: {b.notes}"
    return {"detail_text": text}
