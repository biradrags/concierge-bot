import logging

from maxo import Dispatcher

from concierge_bot.maxbot.handlers import chat, welcome

logger = logging.getLogger(__name__)


def setup_handlers(dp: Dispatcher) -> None:
    dp.include(welcome.setup())
    dp.include(chat.setup())
    logger.debug("Max handlers wired")
