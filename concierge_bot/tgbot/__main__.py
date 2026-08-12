import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from concierge_bot.config import get_config
from concierge_bot.main_factory import create_dishka
from concierge_bot.tgbot.main_factory import resolve_update_types
from concierge_bot.utils.log import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    cfg = get_config()
    setup_logging(cfg.log_level)
    container = create_dishka()
    try:
        bot = await container.get(Bot)
        dp = await container.get(Dispatcher)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=resolve_update_types(dp))
    finally:
        await container.close()
        logger.info("Polling stopped")


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    run()
