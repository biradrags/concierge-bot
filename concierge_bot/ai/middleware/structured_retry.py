import logging
from collections.abc import Awaitable, Callable

from agent_framework import ChatContext, ChatMiddleware
from agent_framework.exceptions import ChatClientInvalidResponseException

logger = logging.getLogger(__name__)


class StructuredOutputRetryMiddleware(ChatMiddleware):
    def __init__(self, *, max_retries: int = 3) -> None:
        self._max_retries = max_retries

    async def process(
        self,
        _context: ChatContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        for attempt in range(1, self._max_retries + 1):
            try:
                await call_next()
            except ChatClientInvalidResponseException as e:
                if attempt >= self._max_retries:
                    raise
                logger.warning(
                    "structured output retry",
                    extra={
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "err": str(e),
                    },
                )
            else:
                return
