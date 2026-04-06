from typing import Any

from maxo import Bot as MaxBot
from maxo.integrations.dishka import CONTAINER_NAME
from maxo.omit import is_defined
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.updates.bot_started import BotStarted
from maxo.routing.updates.message_created import MessageCreated

from concierge_bot.dao import HolderDao
from concierge_bot.services.guest import GuestService


def _locale(update: BotStarted | MessageCreated) -> str:
    if is_defined(update.user_locale):
        return str(update.user_locale)[:16]
    return "en"


async def _attach_hotel_guest(
    ctx: Ctx,
    platform_user_id: int,
    display_name: str | None,
    locale: str,
) -> None:
    container = ctx.get(CONTAINER_NAME)
    bot = ctx.get("bot")
    if container is None or not isinstance(bot, MaxBot):
        return
    dao = await container.get(HolderDao)
    guest_service = GuestService(dao)
    hotel = await dao.hotel.get_by_max_bot_token(bot.token)
    ctx["hotel"] = hotel
    ctx["guest"] = None
    if hotel is None:
        return
    guest = await guest_service.get_or_create(
        platform_user_id,
        hotel.id,
        display_name,
        locale,
    )
    ctx["guest"] = guest


class ConciergeBotStartedMiddleware(BaseMiddleware[BotStarted]):
    async def __call__(
        self,
        update: BotStarted,
        ctx: Ctx,
        next: NextMiddleware[BotStarted],
    ) -> Any:
        await _attach_hotel_guest(
            ctx,
            update.user.user_id,
            update.user.first_name,
            _locale(update),
        )
        return await next(ctx)


class ConciergeMessageCreatedMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        sender = update.message.sender
        if not is_defined(sender):
            ctx["hotel"] = None
            ctx["guest"] = None
            return await next(ctx)
        await _attach_hotel_guest(
            ctx,
            sender.user_id,
            sender.first_name,
            _locale(update),
        )
        return await next(ctx)
