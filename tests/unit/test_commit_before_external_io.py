"""D5: транзакция закрывается до Telegram- и LLM-вызовов (idle_in_transaction 60 с)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO, ServiceDTO
from concierge_bot.services.booking import BookingService
from concierge_bot.services.concierge import ConciergeService


def _hotel() -> HotelDTO:
    return HotelDTO(
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


def _guest(hotel_id) -> GuestDTO:  # noqa: ANN001
    return GuestDTO(
        id=uuid4(),
        telegram_user_id=777,
        hotel_id=hotel_id,
        name="G",
        language_code="en",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )


def _booking(guest_id, service_id, status="pending") -> BookingDTO:  # noqa: ANN001
    return BookingDTO(
        id=uuid4(),
        guest_id=guest_id,
        service_id=service_id,
        status=status,
        notes=None,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_create_booking_commits_before_admin_notification() -> None:
    order = MagicMock()
    hotel = _hotel()
    guest = _guest(hotel.id)
    service = ServiceDTO(
        id=uuid4(),
        hotel_id=hotel.id,
        name="Spa",
        category="spa",
        description=None,
        price=None,
        currency="USD",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    dao = MagicMock()
    dao.service.get_by_id = AsyncMock(return_value=service)
    dao.booking.create = AsyncMock(return_value=_booking(guest.id, service.id))
    order.commit = AsyncMock()
    order.notify_admin = AsyncMock()
    dao.commit = order.commit
    notification = MagicMock()
    notification.notify_admin = order.notify_admin

    await BookingService(dao, notification, MagicMock()).create_booking(guest, service.id, hotel, None)

    assert [c[0] for c in order.mock_calls] == ["commit", "notify_admin"]  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "status"), [("confirm_booking", "confirmed"), ("cancel_booking", "cancelled")])
async def test_status_change_commits_before_guest_notification(method: str, status: str) -> None:
    order = MagicMock()
    guest = _guest(uuid4())
    pending = _booking(guest.id, uuid4())
    pending_with_guest = MagicMock(guest=guest, guest_id=guest.id)
    dao = MagicMock()
    dao.booking.get_by_id = AsyncMock(return_value=pending_with_guest)
    dao.booking.update_status = AsyncMock(return_value=pending.model_copy(update={"status": status}))
    order.commit = AsyncMock()
    order.notify_guest = AsyncMock()
    dao.commit = order.commit
    notification = MagicMock()
    notification.notify_guest = order.notify_guest

    await getattr(BookingService(dao, notification, MagicMock()), method)(pending.id)

    assert [c[0] for c in order.mock_calls] == ["commit", "notify_guest"]  # noqa: S101


@pytest.mark.asyncio
async def test_concierge_commits_before_llm_call() -> None:
    order = MagicMock()
    order.commit = AsyncMock()
    order.agent = AsyncMock(return_value=MagicMock(message="hi"))
    dao = MagicMock()
    dao.commit = order.commit
    config = MagicMock(openai_api_key="sk-test")
    hotel = _hotel()
    service = ConciergeService(dao, MagicMock(), MagicMock(), config, MagicMock(), MagicMock(), MagicMock())

    with patch("concierge_bot.services.concierge.run_concierge_agent", order.agent):
        reply = await service.handle_message(hotel, _guest(hotel.id), "hello")

    assert reply == "hi"  # noqa: S101
    assert [c[0] for c in order.mock_calls][:2] == ["commit", "agent"]  # noqa: S101
