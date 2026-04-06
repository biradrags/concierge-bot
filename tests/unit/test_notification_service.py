from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO, ServiceDTO
from concierge_bot.services.notification import NotificationService


@pytest.mark.asyncio
async def test_notify_admin(mock_bot: MagicMock) -> None:
    svc = NotificationService(mock_bot)
    hotel = HotelDTO(
        id=uuid4(),
        name="H",
        admin_chat_id=500,
        forum_chat_id=None,
        bot_token="t",
        max_bot_token=None,
        system_prompt=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    guest = GuestDTO(
        id=uuid4(),
        telegram_user_id=900,
        hotel_id=hotel.id,
        name="Ivan",
        language_code="en",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )
    service = ServiceDTO(
        id=uuid4(),
        hotel_id=hotel.id,
        name="Dinner",
        category="restaurant",
        description=None,
        price=None,
        currency="USD",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    booking = BookingDTO(
        id=uuid4(),
        guest_id=guest.id,
        service_id=service.id,
        status="pending",
        notes="2 people",
        created_at=datetime.now(UTC),
    )

    await svc.notify_admin(hotel, booking, service, guest)

    mock_bot.send_message.assert_awaited_once_with(
        500,
        mock_bot.send_message.call_args[0][1],
        parse_mode="HTML",
    )
    text = mock_bot.send_message.call_args[0][1]
    assert "Ivan" in text
    assert "Dinner" in text
    assert "pending" in text
    assert "2 people" in text


@pytest.mark.asyncio
async def test_notify_guest(mock_bot: MagicMock) -> None:
    svc = NotificationService(mock_bot)
    guest = GuestDTO(
        id=uuid4(),
        telegram_user_id=111,
        hotel_id=uuid4(),
        name=None,
        language_code="en",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )
    booking = BookingDTO(
        id=uuid4(),
        guest_id=guest.id,
        service_id=uuid4(),
        status="confirmed",
        notes=None,
        created_at=datetime.now(UTC),
    )

    await svc.notify_guest(guest, booking, "confirmed")

    mock_bot.send_message.assert_awaited_once_with(
        111,
        mock_bot.send_message.call_args[0][1],
        parse_mode="HTML",
    )
    assert str(booking.id) in mock_bot.send_message.call_args[0][1]
