from collections.abc import AsyncIterable

from agent_framework.openai import OpenAIChatClient
from aiogram import Bot
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from concierge_bot.ai.history import ConciergeRedisHistoryProvider
from concierge_bot.config import BaseConfig
from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService
from concierge_bot.services.concierge import ConciergeService
from concierge_bot.services.forum import ForumService
from concierge_bot.services.guest import GuestService
from concierge_bot.services.notification import NotificationService


class RequestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        pool: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        async with pool() as sess:
            yield sess

    @provide(scope=Scope.REQUEST)
    def dao(self, session: AsyncSession) -> HolderDao:
        return HolderDao(session)

    @provide(scope=Scope.REQUEST)
    def notification_service(self, bot: Bot) -> NotificationService:
        return NotificationService(bot)

    @provide(scope=Scope.REQUEST)
    def forum_service(self, bot: Bot) -> ForumService:
        return ForumService(bot)

    @provide(scope=Scope.REQUEST)
    def guest_service(self, dao: HolderDao) -> GuestService:
        return GuestService(dao)

    @provide(scope=Scope.REQUEST)
    def booking_service(
        self,
        dao: HolderDao,
        notification: NotificationService,
        forum: ForumService,
    ) -> BookingService:
        return BookingService(dao, notification, forum)

    @provide(scope=Scope.REQUEST)
    def concierge_service(
        self,
        dao: HolderDao,
        client: OpenAIChatClient,
        history: ConciergeRedisHistoryProvider,
        config: BaseConfig,
        booking_service: BookingService,
        bot: Bot,
        forum: ForumService,
    ) -> ConciergeService:
        return ConciergeService(
            dao,
            client,
            history,
            config,
            booking_service,
            bot,
            forum,
        )
