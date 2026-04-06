from dishka import Provider
from dishka.integrations.aiogram import AiogramProvider

from concierge_bot.ai.di import AIProvider
from concierge_bot.di.app_provider import AppProvider
from concierge_bot.di.max_provider import MaxBotProvider, MaxDpProvider
from concierge_bot.di.request_provider import RequestProvider
from concierge_bot.di.tg_provider import TgProvider


def get_tgbot_providers() -> list[Provider]:
    return [
        AiogramProvider(),
        AppProvider(),
        AIProvider(),
        TgProvider(),
        RequestProvider(),
    ]


def get_maxbot_providers() -> list[Provider]:
    return [
        AppProvider(),
        AIProvider(),
        MaxBotProvider(),
        MaxDpProvider(),
        RequestProvider(),
    ]


def get_providers() -> list[Provider]:
    return get_tgbot_providers()
