from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from concierge_bot.dto import GuestDTO, HotelDTO
from concierge_bot.services.booking import BookingService
from concierge_bot.services.forum import ForumService
from concierge_bot.services.notification import NotificationService


@pytest.fixture
def mock_holder_dao() -> MagicMock:
    dao = MagicMock()
    dao.service = MagicMock()
    dao.booking = MagicMock()
    dao.guest = MagicMock()
    return dao


@pytest.fixture
def booking_service(
    mock_holder_dao: MagicMock,
    notification_service: NotificationService,
    forum_service: ForumService,
) -> BookingService:
    return BookingService(mock_holder_dao, notification_service, forum_service)


@pytest.mark.asyncio
async def test_create_booking_service_not_found(
    booking_service: BookingService,
    mock_holder_dao: MagicMock,
) -> None:
    hotel = HotelDTO(
        id=uuid4(),
        name="H",
        admin_chat_id=1,
        forum_chat_id=None,
        bot_token="t",  # noqa: S106
        max_bot_token=None,
        system_prompt=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    guest = GuestDTO(
        id=uuid4(),
        telegram_user_id=1,
        hotel_id=hotel.id,
        name=None,
        language_code="en",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )
    sid = uuid4()
    mock_holder_dao.service.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await booking_service.create_booking(guest, sid, hotel, None)


@pytest.mark.asyncio
async def test_confirm_nonexistent_booking(
    booking_service: BookingService,
    mock_holder_dao: MagicMock,
) -> None:
    mock_holder_dao.booking.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await booking_service.confirm_booking(uuid4())
