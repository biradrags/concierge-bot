from aiogram import Dispatcher
from aiogram_dialog.api.entities import DIALOG_EVENT_NAME

from concierge_bot.tgbot.middlewares.data import ConciergeDataMiddleware
from concierge_bot.tgbot.middlewares.init import InitMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(InitMiddleware())
    m = ConciergeDataMiddleware()
    dp.message.middleware(m)
    dp.callback_query.middleware(m)


def setup_dialog_data_middleware(dp: Dispatcher) -> None:
    dp.observers[DIALOG_EVENT_NAME].middleware(ConciergeDataMiddleware())
