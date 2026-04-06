from dishka import AsyncContainer
from maxo import Dispatcher as MaxDispatcher
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.integrations.dishka import CONTAINER_NAME, setup_dishka

from concierge_bot.maxbot import handlers, middlewares


def create_max_dispatcher(
    container: AsyncContainer,
) -> MaxDispatcher:
    dp = MaxDispatcher(
        key_builder=DefaultKeyBuilder(with_destiny=True),
        disable_fsm=True,
    )
    setup_dishka(container=container, dispatcher=dp, auto_inject=True)
    dp.workflow_data[CONTAINER_NAME] = container
    middlewares.setup_middlewares(dp)
    handlers.setup_handlers(dp)
    return dp
