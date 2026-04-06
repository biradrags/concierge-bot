from typing import Any
from uuid import UUID

from aiogram_dialog import DialogManager

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO
from concierge_bot.shared.categories import CATEGORIES


async def get_categories(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"categories": CATEGORIES}


async def get_services_by_category(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    cat = dialog_manager.dialog_data.get("category")
    if hotel is None or not cat:
        return {"services": []}
    rows = await dao.service.get_by_category(hotel.id, cat)
    items = [{"id": str(s.id), "name": s.name} for s in rows if s.is_active]
    return {"services": items}


async def get_service_detail_guest(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    sid = dialog_manager.dialog_data.get("service_id")
    if not sid:
        return {"detail": "—"}
    s = await dao.service.get_by_id(UUID(sid))
    if s is None:
        return {"detail": "Не найдено"}
    price = f"{s.price} {s.currency}" if s.price is not None else "цена по запросу"
    return {
        "detail": f"<b>{s.name}</b>\n{price}\n{s.description or ''}".strip(),
    }


async def get_booked_done(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"done": "Запрос отправлен администратору."}
