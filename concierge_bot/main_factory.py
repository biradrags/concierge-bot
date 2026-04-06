from dishka import AsyncContainer, make_async_container

from concierge_bot.di import get_tgbot_providers


def create_dishka() -> AsyncContainer:
    return make_async_container(*get_tgbot_providers())
