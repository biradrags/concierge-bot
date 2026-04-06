from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from concierge_bot.dto import BookingDTO, ServiceDTO


class ForumService:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def create_topic(self, forum_chat_id: int, name: str) -> int:
        topic = await self._bot.create_forum_topic(chat_id=forum_chat_id, name=name[:128])
        return int(topic.message_thread_id)

    async def mirror_message(
        self,
        forum_chat_id: int,
        topic_id: int,
        sender: str,
        text: str,
    ) -> None:
        body = f"<b>{sender}</b>\n{text}"
        await self._bot.send_message(
            forum_chat_id,
            body,
            message_thread_id=topic_id,
            parse_mode=ParseMode.HTML,
        )

    async def mirror_booking(
        self,
        forum_chat_id: int,
        topic_id: int,
        booking: BookingDTO,
        service: ServiceDTO,
    ) -> None:
        bid = str(booking.id)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"bk:ok:{bid}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"bk:no:{bid}",
                    ),
                ],
            ],
        )
        text = (
            "<b>Бронь (ожидает решения)</b>\n"
            f"Услуга: {service.name}\n"
            f"ID: <code>{bid}</code>\n"
            f"Статус: {booking.status}"
        )
        if booking.notes:
            text += f"\nЗаметки: {booking.notes}"
        await self._bot.send_message(
            forum_chat_id,
            text,
            message_thread_id=topic_id,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    async def send_to_guest(self, guest_telegram_user_id: int, text: str) -> None:
        await self._bot.send_message(
            guest_telegram_user_id,
            text,
            parse_mode=ParseMode.HTML,
        )
