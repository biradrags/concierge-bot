from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message, TelegramObject
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService
from concierge_bot.services.guest import GuestService


def _chat_user(event: TelegramObject) -> tuple[int | None, Any]:
    if isinstance(event, Message):
        return event.chat.id, event.from_user
    if isinstance(event, CallbackQuery):
        if event.message:
            return event.message.chat.id, event.from_user
        return None, event.from_user
    return None, None


def _private_chat(event: TelegramObject) -> bool:
    if isinstance(event, Message):
        return event.chat.type == ChatType.PRIVATE
    if isinstance(event, CallbackQuery) and event.message:
        return event.message.chat.type == ChatType.PRIVATE
    return False


class ConciergeDataMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        container: AsyncContainer = data[CONTAINER_NAME]
        dao = await container.get(HolderDao)
        bot = await container.get(Bot)
        booking_service = await container.get(BookingService)
        guest_service = await container.get(GuestService)

        hotel = await dao.hotel.get_by_bot_token(bot.token)
        data["hotel"] = hotel
        data["dao"] = dao
        data["booking_service"] = booking_service

        guest = None
        is_admin = False
        chat_id, user = _chat_user(event)
        if hotel is not None and chat_id is not None and user is not None:
            is_admin = chat_id == hotel.admin_chat_id
            if not is_admin and _private_chat(event):
                guest = await guest_service.get_or_create(
                    user.id,
                    hotel.id,
                    user.full_name,
                    (user.language_code or "en")[:16],
                )

        data["guest"] = guest
        data["is_admin"] = is_admin
        return await handler(event, data)
