from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService
from concierge_bot.services.forum import ForumService
from concierge_bot.services.notification import NotificationService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.scalars = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock()
    return session


@pytest.fixture
def mock_bot() -> AsyncMock:
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.create_forum_topic = AsyncMock(
        return_value=MagicMock(message_thread_id=42),
    )
    return bot


@pytest.fixture
def dao(mock_session: AsyncMock) -> HolderDao:
    return HolderDao(mock_session)


@pytest.fixture
def notification_service(mock_bot: AsyncMock) -> NotificationService:
    return NotificationService(mock_bot)


@pytest.fixture
def forum_service(mock_bot: AsyncMock) -> ForumService:
    return ForumService(mock_bot)


@pytest.fixture
def booking_service(
    dao: HolderDao,
    notification_service: NotificationService,
    forum_service: ForumService,
) -> BookingService:
    return BookingService(dao, notification_service, forum_service)
