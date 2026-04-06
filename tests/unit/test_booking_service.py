from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO, ServiceDTO
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


@pytest.fixture
def dao(mock_holder_dao: MagicMock) -> MagicMock:
    return mock_holder_dao


def _hotel() -> HotelDTO:
    return HotelDTO(
        id=uuid4(),
        name="H",
        admin_chat_id=1,
        forum_chat_id=123,
        bot_token="t",
        max_bot_token=None,
        system_prompt=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )


def _guest() -> GuestDTO:
    return GuestDTO(
        id=uuid4(),
        telegram_user_id=777,
        hotel_id=uuid4(),
        name="G",
        language_code="en",
        forum_topic_id=10,
        created_at=datetime.now(UTC),
    )


def _service(hotel_id) -> ServiceDTO:
    return ServiceDTO(
        id=uuid4(),
        hotel_id=hotel_id,
        name="Spa",
        category="spa",
        description=None,
        price=Decimal("50.00"),
        currency="USD",
        is_active=True,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_create_booking(
    booking_service: BookingService,
    dao: MagicMock,
    mock_bot: MagicMock,
) -> None:
    hotel = _hotel()
    guest = _guest()
    guest = guest.model_copy(update={"hotel_id": hotel.id})
    service = _service(hotel.id)
    booking = BookingDTO(
        id=uuid4(),
        guest_id=guest.id,
        service_id=service.id,
        status="pending",
        notes="note",
        created_at=datetime.now(UTC),
    )

    dao.service.get_by_id = AsyncMock(return_value=service)
    dao.booking.create = AsyncMock(return_value=booking)

    result = await booking_service.create_booking(
        guest=guest,
        service_id=service.id,
        hotel=hotel,
        notes="note",
    )

    assert result.status == "pending"
    dao.booking.create.assert_awaited_once()
    mock_bot.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_create_booking_skips_forum_without_topic(
    booking_service: BookingService,
    dao: MagicMock,
    mock_bot: MagicMock,
) -> None:
    hotel = _hotel()
    guest = _guest().model_copy(update={"hotel_id": hotel.id, "forum_topic_id": None})
    service = _service(hotel.id)
    booking = BookingDTO(
        id=uuid4(),
        guest_id=guest.id,
        service_id=service.id,
        status="pending",
        notes=None,
        created_at=datetime.now(UTC),
    )
    dao.service.get_by_id = AsyncMock(return_value=service)
    dao.booking.create = AsyncMock(return_value=booking)

    await booking_service.create_booking(guest, service.id, hotel, None)

    assert mock_bot.send_message.await_count == 1


@pytest.mark.asyncio
async def test_confirm_booking(
    booking_service: BookingService,
    dao: MagicMock,
    mock_bot: MagicMock,
) -> None:
    guest = _guest()
    booking_id = uuid4()
    pending = BookingDTO(
        id=booking_id,
        guest_id=guest.id,
        service_id=uuid4(),
        status="pending",
        notes=None,
        created_at=datetime.now(UTC),
        guest=guest,
    )
    confirmed = pending.model_copy(update={"status": "confirmed"})

    dao.booking.get_by_id = AsyncMock(return_value=pending)
    dao.booking.update_status = AsyncMock(return_value=confirmed)

    result = await booking_service.confirm_booking(booking_id)

    assert result.status == "confirmed"
    dao.booking.update_status.assert_awaited_once_with(booking_id, "confirmed")
    mock_bot.send_message.assert_awaited()


@pytest.mark.asyncio
async def test_cancel_booking(
    booking_service: BookingService,
    dao: MagicMock,
    mock_bot: MagicMock,
) -> None:
    guest = _guest()
    booking_id = uuid4()
    pending = BookingDTO(
        id=booking_id,
        guest_id=guest.id,
        service_id=uuid4(),
        status="pending",
        notes=None,
        created_at=datetime.now(UTC),
        guest=guest,
    )
    cancelled = pending.model_copy(update={"status": "cancelled"})

    dao.booking.get_by_id = AsyncMock(return_value=pending)
    dao.booking.update_status = AsyncMock(return_value=cancelled)

    result = await booking_service.cancel_booking(booking_id)

    assert result.status == "cancelled"
    dao.booking.update_status.assert_awaited_once_with(booking_id, "cancelled")
    mock_bot.send_message.assert_awaited()
