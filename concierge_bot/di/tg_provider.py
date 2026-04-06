import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram_dialog import setup_dialogs
from dishka import AsyncContainer, Provider, Scope, provide
from dishka.integrations.aiogram import setup_dishka

from concierge_bot.config import BaseConfig
from concierge_bot.tgbot.dialogs import setup_concierge_dialogs
from concierge_bot.tgbot.handlers import setup_handlers
from concierge_bot.tgbot.middlewares import (
    setup_dialog_data_middleware,
    setup_middlewares,
)

logger = logging.getLogger(__name__)


class TgProvider(Provider):
    scope = Scope.APP

    @provide
    def fsm_storage(self) -> BaseStorage:
        return MemoryStorage()

    @provide
    def dispatcher(
        self,
        container: AsyncContainer,
        storage: BaseStorage,
    ) -> Dispatcher:
        dp = Dispatcher(storage=storage)
        setup_dishka(container=container, router=dp)
        setup_middlewares(dp)
        setup_dialogs(dp)
        setup_dialog_data_middleware(dp)
        setup_concierge_dialogs(dp)
        setup_handlers(dp)
        logger.info("Telegram dispatcher configured")
        return dp

    @provide
    def telegram_webhook_handler(
        self,
        dp: Dispatcher,
        bot: Bot,
        config: BaseConfig,
    ) -> SimpleRequestHandler:
        secret = config.webhook_secret.strip() or None
        return SimpleRequestHandler(dp, bot, secret_token=secret)
