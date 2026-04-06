from aiogram import Bot
from aiogram.enums import ParseMode

from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO, ServiceDTO


class NotificationService:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def notify_admin(
        self,
        hotel: HotelDTO,
        booking: BookingDTO,
        service: ServiceDTO,
        guest: GuestDTO,
    ) -> None:
        guest_label = guest.name or str(guest.telegram_user_id)
        text = (
            "<b>Новая бронь</b>\n"
            f"Гость: {guest_label}\n"
            f"Услуга: {service.name}\n"
            f"Статус: {booking.status}\n"
            f"ID брони: <code>{booking.id}</code>"
        )
        if booking.notes:
            text += f"\nЗаметки: {booking.notes}"
        await self._bot.send_message(
            hotel.admin_chat_id,
            text,
            parse_mode=ParseMode.HTML,
        )

    async def notify_guest(
        self,
        guest: GuestDTO,
        booking: BookingDTO,
        status: str,
    ) -> None:
        text = (
            "<b>Статус брони обновлён</b>\n"
            f"Бронь <code>{booking.id}</code>: {status}"
        )
        await self._bot.send_message(
            guest.telegram_user_id,
            text,
            parse_mode=ParseMode.HTML,
        )
