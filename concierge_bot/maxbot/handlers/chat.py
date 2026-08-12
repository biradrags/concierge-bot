import html
import logging
from typing import Any

from maxo import Bot as MaxBot
from maxo import Router
from maxo.enums import TextFormat
from maxo.integrations.dishka import inject
from maxo.routing.ctx import Ctx
from maxo.routing.filters import Command, CommandStart
from maxo.routing.updates.message_created import MessageCreated

from concierge_bot.dao import HolderDao
from concierge_bot.dto import GuestDTO
from concierge_bot.services.concierge import ConciergeService

logger = logging.getLogger(__name__)


def _reply_chat_kw(message: MessageCreated) -> dict[str, Any]:
    r = message.message.recipient
    if r.chat_id is not None:
        return {"chat_id": r.chat_id}
    if r.user_id is not None:
        return {"user_id": r.user_id}
    return {}


async def cmd_start(update: MessageCreated, ctx: Ctx) -> None:
    bot: MaxBot = ctx["bot"]
    hotel = ctx.get("hotel")
    kw = _reply_chat_kw(update)
    if not kw:
        return
    if hotel is None:
        await bot.send_message(
            **kw,
            text=(
                "<b>Отель не найден</b>\n"
                "Токен MAX в окружении не совпадает с колонкой "
                "<code>max_bot_token</code> ни в одной записи отеля."
            ),
            format=TextFormat.HTML,
        )
        return
    text = (
        f"<b>{html.escape(hotel.name)}</b>\n"
        "Я помогу с услугами и бронированием. Просто напишите запрос.\n"
        "/mybookings — список броней\n"
        "/admin — админка (Telegram)"
    )
    await bot.send_message(**kw, text=text, format=TextFormat.HTML)


@inject
async def cmd_mybookings(
    update: MessageCreated,
    ctx: Ctx,
    dao: HolderDao,
) -> None:
    bot: MaxBot = ctx["bot"]
    hotel = ctx.get("hotel")
    guest = ctx.get("guest")
    kw = _reply_chat_kw(update)
    if not kw or hotel is None or guest is None:
        return
    lines = await _format_bookings(dao, guest)
    await bot.send_message(**kw, text=lines, format=TextFormat.HTML)


async def _format_bookings(dao: HolderDao, guest: GuestDTO) -> str:
    rows = await dao.booking.get_by_guest(guest.id)
    if not rows:
        return "<b>Брони</b>\nПока нет активных записей."
    parts = ["<b>Ваши брони</b>"]
    for b in rows[:20]:
        sname = html.escape(b.service.name if b.service else str(b.service_id))
        parts.append(
            f"• {sname} — <code>{html.escape(b.status)}</code> — <code>{b.id}</code>"
        )
    return "\n".join(parts)


async def cmd_admin(update: MessageCreated, ctx: Ctx) -> None:
    bot: MaxBot = ctx["bot"]
    kw = _reply_chat_kw(update)
    if not kw:
        return
    await bot.send_message(
        **kw,
        text=(
            "<b>Админка</b>\n"
            "Управление бронями и форумом доступно в Telegram-боте отеля."
        ),
        format=TextFormat.HTML,
    )


@inject
async def on_user_text(
    update: MessageCreated,
    ctx: Ctx,
    concierge: ConciergeService,
) -> None:
    raw = update.message.body.text
    text = (raw or "").strip()
    if not text or text.startswith("/"):
        return
    hotel = ctx.get("hotel")
    guest = ctx.get("guest")
    bot: MaxBot = ctx["bot"]
    kw = _reply_chat_kw(update)
    if not kw:
        return
    if hotel is None:
        await bot.send_message(
            **kw,
            text="Отель не настроен для этого MAX-бота.",
            format=TextFormat.HTML,
        )
        return
    if guest is None:
        await bot.send_message(
            **kw,
            text="Не удалось определить профиль гостя.",
            format=TextFormat.HTML,
        )
        return
    try:
        reply = await concierge.handle_message(hotel, guest, text)
        await bot.send_message(**kw, text=reply, format=TextFormat.HTML)
    except Exception:
        logger.exception("max concierge message failed")
        await bot.send_message(
            **kw,
            text="Сейчас не получилось ответить. Попробуйте позже.",
            format=TextFormat.HTML,
        )


def setup() -> Router:
    router = Router(name=__name__)
    router.message_created.handler(cmd_start, CommandStart())
    router.message_created.handler(cmd_mybookings, Command("mybookings"))
    router.message_created.handler(cmd_admin, Command("admin"))
    router.message_created.handler(on_user_text)
    return router
