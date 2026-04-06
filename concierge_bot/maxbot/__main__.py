"""VK Max long polling: python -m concierge_bot.maxbot"""

import asyncio
import logging
import sys

from maxo import Bot as MaxBot
from maxo import Dispatcher as MaxDispatcher
from maxo.transport.long_polling import LongPolling

from concierge_bot.config import get_config
from concierge_bot.maxbot.main_factory import create_max_dishka
from concierge_bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def _run_long_polling() -> None:
    container = create_max_dishka()
    bot: MaxBot | None = await container.get(MaxBot | None)
    dp: MaxDispatcher = await container.get(MaxDispatcher)
    if bot is None:
        logger.info("MAX_BOT_TOKEN пуст — max-бот не запускается.")
        await container.close()
        return
    lp = LongPolling(dp)
    try:
        await lp.start(bot, drop_pending_updates=True)
    finally:
        await container.close()


def run() -> None:
    cfg = get_config()
    setup_logging(cfg.log_level)
    if not (cfg.max_bot_token or "").strip():
        logger.info("MAX_BOT_TOKEN не задан — max-бот не запускается.")
        return
    try:
        asyncio.run(_run_long_polling())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    run()
