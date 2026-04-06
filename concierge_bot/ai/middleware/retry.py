import asyncio
import logging
from collections.abc import Awaitable, Callable

from agent_framework import AgentContext, AgentMiddleware
from agent_framework.exceptions import (
    ChatClientContentFilterException,
    ChatClientException,
)

from concierge_bot.ai.utils.history import force_strip_dangling_calls

logger = logging.getLogger(__name__)

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAYS = (0.5, 1.5)

HISTORY_ERROR_MARKERS = (
    "No tool call found",
    "tool_call_id",
    "function call output",
)


def is_retriable_history_error(exc: BaseException) -> bool:
    if not isinstance(exc, ChatClientException):
        return False
    msg = str(exc).lower()
    return any(m.lower() in msg for m in HISTORY_ERROR_MARKERS)


class RetryMiddleware(AgentMiddleware):
    def __init__(
        self,
        *,
        max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS,
        retry_if: Callable[[BaseException], bool],
        user_id: int | None = None,
    ) -> None:
        self._max_attempts = max_attempts
        self._delays = delays
        self._retry_if = retry_if
        self._user_id = user_id

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        last_exc: BaseException | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                await call_next()
                return
            except ChatClientContentFilterException:
                raise
            except BaseException as e:
                last_exc = e
                if attempt < self._max_attempts and self._retry_if(e):
                    if is_retriable_history_error(e):
                        force_strip_dangling_calls.set(True)
                    delay = (
                        self._delays[attempt - 1]
                        if attempt - 1 < len(self._delays)
                        else self._delays[-1]
                    )
                    logger.warning(
                        "Agent %s retry in %.1fs (%s/%s): %s",
                        context.agent.name,
                        delay,
                        attempt,
                        self._max_attempts,
                        e,
                        extra={"user_id": self._user_id},
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
        if last_exc:
            raise last_exc
