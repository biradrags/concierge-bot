from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO
from concierge_bot.shared.states import AdminServicesSG


async def on_select_service(
    _: CallbackQuery,
    widget: Any,  # noqa: ARG001
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["service_id"] = item_id
    await manager.switch_to(AdminServicesSG.edit)


async def on_delete_service(
    _: CallbackQuery,
    __: Button,
    manager: DialogManager,
) -> None:
    dao: HolderDao = manager.middleware_data["dao"]
    hotel: HotelDTO | None = manager.middleware_data.get("hotel")
    sid = manager.dialog_data.get("service_id")
    if hotel and sid:
        await dao.service.delete(UUID(sid))
        await dao.commit()
    await manager.switch_to(AdminServicesSG.list)


async def on_add_name(
    m: Message,
    _: ManagedTextInput[str],
    manager: DialogManager,
    __: str,
) -> None:
    manager.dialog_data["new_name"] = (m.text or "").strip()[:255]
    await manager.switch_to(AdminServicesSG.add_category)


async def on_pick_category(
    _: CallbackQuery,
    widget: Any,  # noqa: ARG001
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["new_category"] = item_id
    await manager.switch_to(AdminServicesSG.add_description)


async def on_add_description(
    m: Message,
    _: ManagedTextInput[str],
    manager: DialogManager,
    __: str,
) -> None:
    t = (m.text or "").strip()
    manager.dialog_data["new_description"] = (
        None if t in {"", "-"} else t[:2000]
    )
    await manager.switch_to(AdminServicesSG.add_price)


async def on_add_price(
    m: Message,
    _: ManagedTextInput[str],
    manager: DialogManager,
    __: str,
) -> None:
    raw = (m.text or "").strip().replace(",", ".")
    if raw in {"", "-"}:
        manager.dialog_data["new_price"] = None
        await manager.switch_to(AdminServicesSG.confirm)
        return
    try:
        price = Decimal(raw)
    except InvalidOperation:
        price = None
    manager.dialog_data["new_price"] = str(price) if price is not None else None
    await manager.switch_to(AdminServicesSG.confirm)


async def on_confirm_add(
    _: CallbackQuery,
    __: Button,
    manager: DialogManager,
) -> None:
    dao: HolderDao = manager.middleware_data["dao"]
    hotel: HotelDTO | None = manager.middleware_data.get("hotel")
    if not hotel:
        await manager.switch_to(AdminServicesSG.list)
        return
    name = manager.dialog_data.get("new_name")
    cat = manager.dialog_data.get("new_category")
    if not name or not cat:
        await manager.switch_to(AdminServicesSG.list)
        return
    desc = manager.dialog_data.get("new_description")
    price_raw = manager.dialog_data.get("new_price")
    price: Decimal | None
    try:
        price = Decimal(price_raw) if price_raw else None
    except (InvalidOperation, TypeError):
        price = None
    await dao.service.create(
        hotel_id=hotel.id,
        name=name,
        category=cat,
        description=desc,
        price=price,
    )
    await dao.commit()
    manager.dialog_data.pop("new_name", None)
    manager.dialog_data.pop("new_category", None)
    manager.dialog_data.pop("new_description", None)
    manager.dialog_data.pop("new_price", None)
    await manager.switch_to(AdminServicesSG.list)
