import html
from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService

router = Router(name="booking_callback")


@router.callback_query(F.data.startswith("bk:"))
@inject
async def on_booking_decision(
    query: CallbackQuery,
    booking_service: FromDishka[BookingService],
    dao: FromDishka[HolderDao],
) -> None:
    if not query.data or not query.message:
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
            await booking_service.confirm_booking(booking_id)
        else:
            await booking_service.cancel_booking(booking_id)
        await dao.commit()
    except ValueError as e:
        await query.answer(str(e), show_alert=True)
        return
    await query.answer("Готово")
    if not query.message:
        return
    base = query.message.text or query.message.caption or ""
    status_ru = "подтверждена" if action == "ok" else "отклонена"
    suffix = f"\n\n<b>Статус:</b> {html.escape(status_ru)}"
    try:
        if query.message.text is not None:
            await query.message.edit_text(
                f"{html.escape(base)}{suffix}",
                parse_mode=ParseMode.HTML,
                reply_markup=None,
            )
        else:
            await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        await query.message.edit_reply_markup(reply_markup=None)
