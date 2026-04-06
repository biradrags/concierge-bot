from aiogram import Dispatcher

from concierge_bot.tgbot.handlers import (
    admin,
    booking_callback,
    forum,
    message,
    my_bookings,
    start,
)


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(my_bookings.router)
    dp.include_router(forum.router)
    dp.include_router(booking_callback.router)
    dp.include_router(message.router)
