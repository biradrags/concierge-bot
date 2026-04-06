from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from aiogram.types import InlineKeyboardButton

from concierge_bot.dto import BookingDTO, ServiceDTO
from concierge_bot.services.forum import ForumService


@pytest.mark.asyncio
async def test_create_topic(mock_bot: MagicMock) -> None:
    svc = ForumService(mock_bot)
    tid = await svc.create_topic(1000, "Topic name here")

    assert tid == 42
    mock_bot.create_forum_topic.assert_awaited_once_with(
        chat_id=1000,
        name="Topic name here"[:128],
    )


@pytest.mark.asyncio
async def test_mirror_message(mock_bot: MagicMock) -> None:
    svc = ForumService(mock_bot)
    await svc.mirror_message(5, 7, "Guest", "hello")

    mock_bot.send_message.assert_awaited_once_with(
        5,
        "<b>Guest</b>\nhello",
        message_thread_id=7,
        parse_mode="HTML",
    )


@pytest.mark.asyncio
async def test_mirror_booking(mock_bot: MagicMock) -> None:
    svc = ForumService(mock_bot)
    booking = BookingDTO(
        id=uuid4(),
        guest_id=uuid4(),
        service_id=uuid4(),
        status="pending",
        notes="x",
        created_at=datetime.now(UTC),
    )
    service = ServiceDTO(
        id=booking.service_id,
        hotel_id=uuid4(),
        name="Massage",
        category="spa",
        description=None,
        price=Decimal("1"),
        currency="USD",
        is_active=True,
        created_at=datetime.now(UTC),
    )

    await svc.mirror_booking(1, 2, booking, service)

    mock_bot.send_message.assert_awaited_once()
    kwargs = mock_bot.send_message.call_args.kwargs
    assert kwargs["message_thread_id"] == 2
    kb = kwargs["reply_markup"]
    assert kb.inline_keyboard
    row = kb.inline_keyboard[0]
    assert isinstance(row[0], InlineKeyboardButton)
    assert row[0].callback_data.startswith("bk:ok:")
    assert row[1].callback_data.startswith("bk:no:")
