import html
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.services.forum import ForumService

logger = logging.getLogger(__name__)

router = Router(name="forum")


@router.message(
    F.chat.type == ChatType.SUPERGROUP,
    F.message_thread_id,
    F.text,
    ~F.text.startswith("/"),
)
@inject
async def relay_forum_topic_to_guest(
    message: Message,
    bot: Bot,
    dao: FromDishka[HolderDao],
    forum: FromDishka[ForumService],
) -> None:
    if not message.text or message.from_user is None or message.from_user.is_bot:
        return
    if message.from_user.id == bot.id:
        return
    tid = message.message_thread_id
    if tid is None:
        return
    hotel = await dao.hotel.get_by_forum_chat_id(message.chat.id)
    if hotel is None:
        return
    guest = await dao.guest.get_by_forum_thread(message.chat.id, tid)
    if guest is None:
        return
    label = message.from_user.full_name or str(message.from_user.id)
    body = (
        f"<b>{html.escape(label)}</b> (ответ отеля)\n"
        f"{html.escape(message.text)}"
    )
    try:
        await forum.send_to_guest(guest.telegram_user_id, body)
    except Exception:
        logger.exception("forum relay to guest failed")
