"""D5: транзакция закрывается до Telegram- и LLM-вызовов (idle_in_transaction 60 с)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from concierge_bot.services.booking import BookingService
from concierge_bot.services.concierge import ConciergeService
from tests.unit.factories import make_booking, make_guest, make_hotel, make_service


@pytest.mark.asyncio
async def test_create_booking_commits_before_admin_notification() -> None:
    order = MagicMock()
    hotel = make_hotel()
    guest = make_guest(hotel.id)
    service = make_service(hotel.id)
    dao = MagicMock()
    dao.service.get_by_id = AsyncMock(return_value=service)
    dao.booking.create = AsyncMock(return_value=make_booking(guest.id, service.id))
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
    guest = make_guest(uuid4())
    pending = make_booking(guest.id, uuid4())
    dao = MagicMock()
    dao.booking.get_by_id = AsyncMock(return_value=pending.model_copy(update={"guest": guest}))
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
    hotel = make_hotel()
    service = ConciergeService(dao, MagicMock(), MagicMock(), config, MagicMock(), MagicMock(), MagicMock())

    with patch("concierge_bot.services.concierge.run_concierge_agent", order.agent):
        reply = await service.handle_message(hotel, make_guest(hotel.id), "hello")

    assert reply == "hi"  # noqa: S101
    assert [c[0] for c in order.mock_calls][:2] == ["commit", "agent"]  # noqa: S101
