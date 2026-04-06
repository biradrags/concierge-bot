from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.services.forum import ForumService
from concierge_bot.services.guest import GuestService

router = Router(name="start")


@router.message(CommandStart())
@inject
async def cmd_start(
    message: Message,
    bot: Bot,
    dao: FromDishka[HolderDao],
    guest_service: FromDishka[GuestService],
    forum: FromDishka[ForumService],
) -> None:
    hotel = await dao.hotel.get_by_bot_token(bot.token)
    if hotel is None:
        await message.answer("Этот бот не привязан к отелю в базе (bot_token).")
        return

    if message.chat.id == hotel.admin_chat_id:
        await message.answer(
            "Админ-чат отеля. Новые брони приходят сюда; подтверждение — кнопками в теме форума.\n"
            "В личке с ботом: /admin — панель управления.",
        )
        return

    if message.chat.type != "private":
        await message.answer("Откройте диалог с ботом в личных сообщениях и нажмите /start.")
        return

    if message.from_user is None:
        return

    lang = (message.from_user.language_code or "en")[:16]
    guest = await guest_service.get_or_create(
        telegram_user_id=message.from_user.id,
        hotel_id=hotel.id,
        name=message.from_user.full_name,
        language_code=lang,
    )
    if hotel.forum_chat_id is not None and guest.forum_topic_id is None:
        topic_id = await forum.create_topic(
            hotel.forum_chat_id,
            (message.from_user.full_name or str(message.from_user.id))[:120],
        )
        await dao.guest.update_forum_topic_id(guest.id, topic_id)
        await dao.commit()

    await message.answer(
        f"Добро пожаловать в <b>{hotel.name}</b>! Напишите, чем помочь — экскурсии, столик, трансфер.\n"
        "/mybookings — ваши брони.",
    )
