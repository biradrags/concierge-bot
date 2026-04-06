import logging
from collections.abc import Sequence
from typing import Any

from agent_framework import Message
from agent_framework_redis import RedisHistoryProvider

from concierge_bot.ai.utils.history import (
    _normalize_messages_for_openai,
    _trim_by_turns,
    assert_max_messages_positive,
    sanitize_messages,
)
from concierge_bot.config import BaseConfig

logger = logging.getLogger(__name__)

KEY_PREFIX = "concierge"
HISTORY_TURNS = 8
MAX_MESSAGES = 100


class ConciergeRedisHistoryProvider(RedisHistoryProvider):
    async def get_messages(
        self,
        session_id: str | None,
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        raw = await super().get_messages(session_id, state=state, **kwargs)
        sanitized = sanitize_messages(raw)
        normalized = _normalize_messages_for_openai(sanitized)
        trimmed = _trim_by_turns(normalized, HISTORY_TURNS, self.max_messages)
        if trimmed and logger.isEnabledFor(logging.DEBUG):
            logger.debug("concierge history session=%s count=%s", session_id, len(trimmed))
        return trimmed

    async def save_messages(
        self,
        session_id: str | None,
        messages: Sequence[Message],
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        stripped = _normalize_messages_for_openai(list(messages))
        await super().save_messages(session_id, stripped, state=state, **kwargs)


def build_concierge_history_provider(config: BaseConfig) -> ConciergeRedisHistoryProvider:
    assert_max_messages_positive(MAX_MESSAGES)
    return ConciergeRedisHistoryProvider(
        source_id="redis_concierge_memory",
        redis_url=config.redis_url,
        key_prefix=KEY_PREFIX,
        max_messages=MAX_MESSAGES,
        load_messages=True,
        store_inputs=True,
        store_outputs=True,
        store_context_messages=False,
    )
