"""Stale-intent: старые inline-кнопки после рестарта не сыпят трейсбеки (канон dialogs.md)."""

from aiogram import Router
from bira_core.tgbot.dialogs.errors import register_stale_intent

router = Router(name="errors")
register_stale_intent(router)
