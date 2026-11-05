from collections.abc import AsyncIterable

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bira_core.db.settings import dml_dsn
from bira_core.db.url import DbDsn
from bira_core.redis.client import make_redis_client
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from concierge_bot.config import BaseConfig, get_config


class AppProvider(Provider):
    scope = Scope.APP

    @provide
    def config(self) -> BaseConfig:
        return get_config()

    @provide
    def dsn(self, config: BaseConfig) -> DbDsn:
        return dml_dsn(config)

    @provide
    async def redis(self, config: BaseConfig) -> AsyncIterable[Redis]:
        client = make_redis_client(config.redis_url, decode_responses=False)
        yield client
        await client.aclose()

    @provide
    async def bot(self, config: BaseConfig) -> AsyncIterable[Bot]:
        async with Bot(
            token=config.telegram_bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                allow_sending_without_reply=True,
            ),
        ) as bot:
            yield bot
