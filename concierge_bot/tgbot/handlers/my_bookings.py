import html

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.services.guest import GuestService

router = Router(name="my_bookings")

_STATUS_EMOJI = {
    "pending": "⏳",
    "confirmed": "✅",
    "cancelled": "❌",
}


@router.message(Command("mybookings"))
@inject
async def cmd_mybookings(
    message: Message,
    bot: FromDishka[Bot],
    dao: FromDishka[HolderDao],
    guest_service: FromDishka[GuestService],
) -> None:
    if message.chat.type != "private" or message.from_user is None:
        return
    hotel = await dao.hotel.get_by_bot_token(bot.token)
    if hotel is None:
        await message.answer("Бот не настроен.")
        return
    if message.chat.id == hotel.admin_chat_id:
        return
    lang = (message.from_user.language_code or "en")[:16]
    guest = await guest_service.get_or_create(
        message.from_user.id,
        hotel.id,
        message.from_user.full_name,
        lang,
    )
    rows = await dao.booking.get_by_guest(guest.id)
    if not rows:
        await message.answer("У вас пока нет бронирований.")
        return
    lines = []
    for b in rows:
        em = _STATUS_EMOJI.get(b.status, "•")
        svc = b.service.name if b.service else "услуга"
        lines.append(
            f"{em} {html.escape(svc)} — <code>{b.id}</code> ({html.escape(b.status)})"
        )
    await message.answer(
        "<b>Ваши брони</b>\n" + "\n".join(lines),
    )
