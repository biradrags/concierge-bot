"""Решение по брони из кнопки: ответ на callback всегда, устаревшее сообщение не оставляет тихий выход."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.types import CallbackQuery, Chat, InaccessibleMessage, Message

from concierge_bot.tgbot.handlers.booking_callback import on_booking_decision


def _query(message: object) -> MagicMock:
    query = MagicMock(spec=CallbackQuery)
    query.data = f"bk:ok:{uuid4()}"
    query.message = message
    query.answer = AsyncMock()
    return query


def _service() -> MagicMock:
    service = MagicMock()
    service.confirm_booking = AsyncMock()
    service.cancel_booking = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_inaccessible_message_still_answers_with_alert() -> None:
    query = _query(InaccessibleMessage(chat=Chat(id=1, type="private"), message_id=5))
    service = _service()

    await on_booking_decision(query, service)

    service.confirm_booking.assert_awaited_once()
    query.answer.assert_awaited_once()
    assert query.answer.await_args.kwargs.get("show_alert") is True  # noqa: S101


@pytest.mark.asyncio
async def test_missing_message_answers_instead_of_silence() -> None:
    query = _query(None)
    service = _service()

    await on_booking_decision(query, service)

    query.answer.assert_awaited_once()
    service.confirm_booking.assert_not_awaited()


@pytest.mark.asyncio
async def test_accessible_message_edits_and_answers() -> None:
    message = MagicMock(spec=Message)
    message.text = "Новая бронь"
    message.caption = None
    message.edit_text = AsyncMock()
    query = _query(message)

    await on_booking_decision(query, _service())

    query.answer.assert_awaited_once_with("Готово")
    message.edit_text.assert_awaited_once()
