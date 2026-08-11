"""Stale-intent хендлеры: после рестарта/деплоя старые inline-кнопки не должны сыпать трейсбеки.

Канон: ~/.claude/rules/dialogs.md -> "Stale-intent (UnknownIntent / OutdatedIntent)".
"""

import logging

from aiogram import Bot, Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.errors(ExceptionTypeFilter(UnknownIntent, OutdatedIntent))
async def on_stale_intent(event: ErrorEvent, bot: Bot) -> bool:
    cb = event.update.callback_query
    if cb is None or cb.message is None:
        return True
    logger.info(
        "Stale intent: dropping chat_id=%s mid=%s",
        cb.message.chat.id,
        cb.message.message_id,
    )
    try:
        await bot.delete_message(chat_id=cb.message.chat.id, message_id=cb.message.message_id)
    except Exception:  # noqa: BLE001 - сообщение могло быть уже удалено, граница фреймворка
        logger.debug("stale intent: delete_message failed", exc_info=True)
    try:
        # Без тоста: пользователь уже видит свежий диалог, alert только путает (канон dialogs.md).
        await cb.answer()
    except Exception:  # noqa: BLE001 - query too old (сам stale-intent случай), граница фреймворка
        logger.debug("stale intent: cb.answer failed", exc_info=True)
    return True
