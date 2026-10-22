import html
from contextlib import suppress
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from concierge_bot.services.booking import BookingService

router = Router(name="booking_callback")

_STATUS_RU = {"confirmed": "подтверждена", "cancelled": "отклонена"}


@router.callback_query(F.data.startswith("bk:"))
async def on_booking_decision(
    query: CallbackQuery,
    booking_service: BookingService,
    bot: Bot,
) -> None:
    if not query.data:
        return
    if not query.message:
        await query.answer("Сообщение недоступно. Откройте бронь через /admin.", show_alert=True)
        return
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Некорректные данные", show_alert=True)
        return
    _, action, bid = parts[0], parts[1], parts[2]
    try:
        booking_id = UUID(bid)
    except ValueError:
        await query.answer("Некорректный id", show_alert=True)
        return
    try:
        if action == "ok":
            booking = await booking_service.confirm_booking(booking_id)
        else:
            booking = await booking_service.cancel_booking(booking_id)
    except ValueError as e:
        await query.answer(str(e), show_alert=True)
        return
    message = query.message
    # старше 48 ч сообщение приходит как InaccessibleMessage: клавиатуру снимаем через bot (dialogs.md, stale-intent)
    if not isinstance(message, Message):
        with suppress(TelegramBadRequest):
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=None)
        await query.answer("Бронь обработана. Сообщение устарело, откройте её заново.", show_alert=True)
        return
    await query.answer("Готово")
    base = message.text or message.caption or ""
    # статус берём из брони: уже решённая раньше бронь не меняется, кнопка могла быть устаревшей
    status_ru = _STATUS_RU.get(booking.status, booking.status)
    suffix = f"\n\n<b>Статус:</b> {html.escape(status_ru)}"
    try:
        if message.text is not None:
            await message.edit_text(
                f"{html.escape(base)}{suffix}",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        else:
            await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        await message.edit_reply_markup(reply_markup=None)
