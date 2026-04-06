from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from concierge_bot.dto import GuestDTO, HotelDTO
from concierge_bot.services.booking import BookingService
from concierge_bot.shared.states import GuestServicesSG


async def on_select_category(
    _: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["category"] = item_id
    await manager.switch_to(GuestServicesSG.list)


async def on_select_service(
    _: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["service_id"] = item_id
    await manager.switch_to(GuestServicesSG.detail)


async def on_book(
    _: CallbackQuery,
    __: Button,
    manager: DialogManager,
) -> None:
    hotel: HotelDTO | None = manager.middleware_data.get("hotel")
    guest: GuestDTO | None = manager.middleware_data.get("guest")
    booking_service: BookingService = manager.middleware_data["booking_service"]
    sid = manager.dialog_data.get("service_id")
    if not hotel or not guest or not sid:
        await manager.switch_to(GuestServicesSG.categories)
        return
    from uuid import UUID

    await booking_service.create_booking(
        guest=guest,
        service_id=UUID(sid),
        hotel=hotel,
        notes=None,
    )
    await manager.middleware_data["dao"].commit()
    await manager.switch_to(GuestServicesSG.booked)
