from aiogram import Dispatcher

from concierge_bot.tgbot.dialogs.admin_bookings.dialogs import admin_bookings_dialog
from concierge_bot.tgbot.dialogs.admin_main.dialogs import admin_main_dialog
from concierge_bot.tgbot.dialogs.admin_prompt.dialogs import admin_prompt_dialog
from concierge_bot.tgbot.dialogs.admin_services.dialogs import admin_services_dialog
from concierge_bot.tgbot.dialogs.admin_stats.dialogs import admin_stats_dialog
from concierge_bot.tgbot.dialogs.guest_services.dialogs import guest_services_dialog


def setup_concierge_dialogs(dp: Dispatcher) -> None:
    dp.include_router(admin_main_dialog)
    dp.include_router(admin_services_dialog)
    dp.include_router(admin_bookings_dialog)
    dp.include_router(admin_prompt_dialog)
    dp.include_router(admin_stats_dialog)
    dp.include_router(guest_services_dialog)
