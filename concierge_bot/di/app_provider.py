from collections.abc import AsyncIterable

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from concierge_bot.config import BaseConfig, get_config


class AppProvider(Provider):
    scope = Scope.APP

    @provide
    def config(self) -> BaseConfig:
        return get_config()

    @provide
    async def engine(self, config: BaseConfig) -> AsyncIterable[AsyncEngine]:
        url = make_url(config.database_url)
        connect_args: dict[str, object] = {}
        host = (url.host or "").lower()
        if host.endswith(".flycast") or host.endswith(".internal"):
            connect_args["ssl"] = False
        eng = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30,
            pool_timeout=5,
            connect_args=connect_args,
        )
        yield eng
        await eng.dispose(True)

    @provide
    def pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    @provide
    async def redis(self, config: BaseConfig) -> AsyncIterable[Redis]:
        client = Redis.from_url(config.redis_url, decode_responses=False)
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
