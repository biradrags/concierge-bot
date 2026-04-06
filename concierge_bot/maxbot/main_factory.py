from dishka import AsyncContainer, make_async_container

from concierge_bot.di import get_maxbot_providers


def create_max_dishka() -> AsyncContainer:
    return make_async_container(*get_maxbot_providers())
