from maxo import Dispatcher

from concierge_bot.maxbot.middlewares.context import (
    ConciergeBotStartedMiddleware,
    ConciergeMessageCreatedMiddleware,
)


def setup_middlewares(dp: Dispatcher) -> None:
    dp.message_created.middleware.outer(ConciergeMessageCreatedMiddleware())
    dp.bot_started.middleware.outer(ConciergeBotStartedMiddleware())
