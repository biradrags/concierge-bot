"""Бронь сохранена: сбой Telegram-уведомления не превращается в ошибку и не даёт дубль."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.exceptions import TelegramForbiddenError

from concierge_bot.services.booking import BookingService
from tests.unit.factories import make_booking, make_guest, make_hotel, make_service


def _forbidden() -> TelegramForbiddenError:
    return TelegramForbiddenError(method=MagicMock(), message="Forbidden: bot was blocked by the user")


@pytest.fixture
def dao() -> MagicMock:
    dao = MagicMock()
    dao.commit = AsyncMock()
    return dao


@pytest.mark.asyncio
@pytest.mark.parametrize("failing", ["notify_admin", "mirror_booking"])
async def test_create_booking_survives_notification_failure(dao: MagicMock, failing: str) -> None:
    hotel = make_hotel().model_copy(update={"forum_chat_id": 5})
    guest = make_guest(hotel.id).model_copy(update={"forum_topic_id": 9})
    service = make_service(hotel.id)
    booking = make_booking(guest.id, service.id)
    dao.service.get_by_id = AsyncMock(return_value=service)
    dao.booking.create = AsyncMock(return_value=booking)
    notification, forum = MagicMock(), MagicMock()
    notification.notify_admin = AsyncMock()
    forum.mirror_booking = AsyncMock()
    getattr(notification if failing == "notify_admin" else forum, failing).side_effect = _forbidden()

    result = await BookingService(dao, notification, forum).create_booking(guest, service.id, hotel, None)

    assert result == booking  # noqa: S101
    dao.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_status_change_survives_guest_notification_failure(dao: MagicMock) -> None:
    guest = make_guest(uuid4())
    updated = make_booking(guest.id, uuid4(), "confirmed")
    pending = updated.model_copy(update={"status": "pending", "guest": guest})
    dao.booking.get_by_id = AsyncMock(return_value=pending)
    dao.booking.update_status = AsyncMock(return_value=updated)
    notification = MagicMock()
    notification.notify_guest = AsyncMock(side_effect=_forbidden())

    result = await BookingService(dao, notification, MagicMock()).confirm_booking(updated.id)

    assert result == updated  # noqa: S101
    dao.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_repeated_decision_is_noop(dao: MagicMock) -> None:
    guest = make_guest(uuid4())
    already = make_booking(guest.id, uuid4(), "confirmed").model_copy(update={"guest": guest})
    dao.booking.get_by_id = AsyncMock(return_value=already)
    dao.booking.update_status = AsyncMock()
    notification = MagicMock()
    notification.notify_guest = AsyncMock()

    result = await BookingService(dao, notification, MagicMock()).confirm_booking(already.id)

    assert result == already  # noqa: S101
    dao.booking.update_status.assert_not_awaited()
    notification.notify_guest.assert_not_awaited()
    dao.commit.assert_not_awaited()
