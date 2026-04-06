import logging

from dishka import AsyncContainer, Provider, Scope, provide
from maxo import Bot as MaxBot
from maxo import Dispatcher as MaxDispatcher

from concierge_bot.config import BaseConfig
from concierge_bot.maxbot.factory import create_max_dispatcher

logger = logging.getLogger(__name__)


class MaxBotProvider(Provider):
    scope = Scope.APP

    @provide
    def max_bot(self, config: BaseConfig) -> MaxBot | None:
        token = (config.max_bot_token or "").strip()
        if not token:
            return None
        return MaxBot(token=token, warming_up=False)


class MaxDpProvider(Provider):
    scope = Scope.APP

    @provide
    def max_dispatcher(
        self,
        container: AsyncContainer,
    ) -> MaxDispatcher:
        dp = create_max_dispatcher(container)
        logger.info("VK Max dispatcher configured")
        return dp
