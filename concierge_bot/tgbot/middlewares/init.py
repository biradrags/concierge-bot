from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService
from concierge_bot.services.concierge import ConciergeService
from concierge_bot.services.forum import ForumService
from concierge_bot.services.guest import GuestService


class InitMiddleware(BaseMiddleware):
    """REQUEST-зависимости апдейта в data из одной области dishka (dialogs.md, «Одна область»).

    Ключи: dao, guest_service, booking_service, forum, concierge."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        dishka: AsyncContainer = data[CONTAINER_NAME]
        data["dao"] = await dishka.get(HolderDao)
        data["guest_service"] = await dishka.get(GuestService)
        data["booking_service"] = await dishka.get(BookingService)
        data["forum"] = await dishka.get(ForumService)
        data["concierge"] = await dishka.get(ConciergeService)
        return await handler(event, data)
