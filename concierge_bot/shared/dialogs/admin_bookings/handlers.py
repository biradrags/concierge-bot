from typing import Any
from uuid import UUID

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from concierge_bot.services.booking import BookingService
from concierge_bot.shared.states import AdminBookingsSG


async def on_select_booking(
    _: CallbackQuery,
    widget: Any,  # noqa: ARG001
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["booking_id"] = item_id
    await manager.switch_to(AdminBookingsSG.detail)


async def on_confirm_booking(
    _: CallbackQuery,
    __: Button,
    manager: DialogManager,
) -> None:
    booking_service: BookingService = manager.middleware_data["booking_service"]
    raw = manager.dialog_data.get("booking_id")
    if raw:
        await booking_service.confirm_booking(UUID(raw))
        await manager.middleware_data["dao"].commit()
    await manager.switch_to(AdminBookingsSG.list)


async def on_cancel_booking(
    _: CallbackQuery,
    __: Button,
    manager: DialogManager,
) -> None:
    booking_service: BookingService = manager.middleware_data["booking_service"]
    raw = manager.dialog_data.get("booking_id")
    if raw:
        await booking_service.cancel_booking(UUID(raw))
        await manager.middleware_data["dao"].commit()
    await manager.switch_to(AdminBookingsSG.list)
