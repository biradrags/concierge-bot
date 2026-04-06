from aiogram import Bot, F, Router
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.services.concierge import ConciergeService
from concierge_bot.services.guest import GuestService

router = Router(name="message")


@router.message(F.text, ~F.text.startswith("/"))
@inject
async def on_guest_text(
    message: Message,
    bot: Bot,
    dao: FromDishka[HolderDao],
    guest_service: FromDishka[GuestService],
    concierge: FromDishka[ConciergeService],
) -> None:
    if message.chat.type != "private" or not message.text or message.from_user is None:
        return

    hotel = await dao.hotel.get_by_bot_token(bot.token)
    if hotel is None or message.chat.id == hotel.admin_chat_id:
        return

    lang = (message.from_user.language_code or "en")[:16]
    guest = await guest_service.get_or_create(
        telegram_user_id=message.from_user.id,
        hotel_id=hotel.id,
        name=message.from_user.full_name,
        language_code=lang,
    )
    reply = await concierge.handle_message(hotel, guest, message.text)
    await message.answer(reply)
