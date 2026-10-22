"""Решение по брони из кнопки: ответ на callback всегда, у устаревшего сообщения клавиатура снимается через bot."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from aiogram.exceptions import TelegramBadRequest
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


def _bot() -> MagicMock:
    bot = MagicMock()
    bot.edit_message_reply_markup = AsyncMock()
    return bot


def _inaccessible() -> InaccessibleMessage:
    return InaccessibleMessage(chat=Chat(id=1, type="private"), message_id=5)


@pytest.mark.asyncio
async def test_inaccessible_message_keyboard_removed_via_bot_and_alert_shown() -> None:
    query, service, bot = _query(_inaccessible()), _service(), _bot()

    await on_booking_decision(query, service, bot)

    service.confirm_booking.assert_awaited_once()
    bot.edit_message_reply_markup.assert_awaited_once_with(chat_id=1, message_id=5, reply_markup=None)
    query.answer.assert_awaited_once()
    assert query.answer.await_args.kwargs.get("show_alert") is True  # noqa: S101


@pytest.mark.asyncio
async def test_inaccessible_message_answer_survives_keyboard_removal_failure() -> None:
    query, bot = _query(_inaccessible()), _bot()
    bot.edit_message_reply_markup.side_effect = TelegramBadRequest(method=MagicMock(), message="message can't be edited")

    await on_booking_decision(query, _service(), bot)

    query.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_message_answers_instead_of_silence() -> None:
    query, service = _query(None), _service()

    await on_booking_decision(query, service, _bot())

    query.answer.assert_awaited_once()
    service.confirm_booking.assert_not_awaited()


@pytest.mark.asyncio
async def test_accessible_message_edits_and_answers() -> None:
    message = MagicMock(spec=Message)
    message.text = "Новая бронь"
    message.caption = None
    message.edit_text = AsyncMock()
    query, bot = _query(message), _bot()

    await on_booking_decision(query, _service(), bot)

    query.answer.assert_awaited_once_with("Готово")
    message.edit_text.assert_awaited_once()
    bot.edit_message_reply_markup.assert_not_awaited()
