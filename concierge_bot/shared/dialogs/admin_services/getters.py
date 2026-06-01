from typing import Any
from uuid import UUID

from aiogram_dialog import DialogManager

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO
from concierge_bot.shared.categories import CATEGORIES


async def get_services_list(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    if hotel is None:
        return {"services": []}
    rows = await dao.service.get_active_by_hotel(hotel.id)
    items = [{"id": str(s.id), "name": s.name} for s in rows]
    return {"services": items}


async def get_service_detail(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    sid = dialog_manager.dialog_data.get("service_id")
    if not sid:
        return {"detail": "—"}
    s = await dao.service.get_by_id(UUID(sid))
    if s is None:
        return {"detail": "Не найдено"}
    price = f"{s.price} {s.currency}" if s.price is not None else "—"
    text = (
        f"<b>{s.name}</b>\n"
        f"Категория: {s.category}\n"
        f"Цена: {price}\n"
        f"Описание: {s.description or '—'}"
    )
    return {"detail": text}


async def get_categories(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    return {"categories": CATEGORIES}


async def get_add_summary(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG001
    name = dialog_manager.dialog_data.get("new_name", "—")
    cat = dialog_manager.dialog_data.get("new_category", "—")
    desc = dialog_manager.dialog_data.get("new_description") or "—"
    price = dialog_manager.dialog_data.get("new_price") or "—"
    return {"summary": f"Название: {name}\nКатегория: {cat}\nОписание: {desc}\nЦена: {price}"}
