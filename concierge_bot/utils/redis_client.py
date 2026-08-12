"""Shared Redis client builder (канон флота, stock-first).

После Fly-suspend (min_machines_running=0) TCP-транспорт разорван; redis-py
переиспользует мёртвый коннект, и следующая команда падает голым TypeError
(transport.writelines на self._write_ready == None), который дефолтный retry
redis-py не ловит (supported_errors по умолчанию - только Connection/Timeout).
Вместо кастомной обёртки расширяем списки исключений ШТАТНОГО Retry: при фейле
redis-py сам дропает коннект и лениво переподключается на повторе.

health_check_interval НЕ используем: его проактивный PING сам пишет в мёртвый
транспорт и падает тем же TypeError вне retry-контура команды.
"""

from __future__ import annotations

import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

DEFAULT_SOCKET_TIMEOUT = 5
DEFAULT_RETRY_ATTEMPTS = 2

# TypeError - Fly-suspend torn transport; OSError - сокет умер между keepalive-пробами
# (builtin TimeoutError - подкласс OSError, покрыт).
_RECONNECT_ERRORS: tuple[type[BaseException], ...] = (
    RedisConnectionError,
    RedisTimeoutError,
    OSError,
    TypeError,
)


def make_redis_client(
    redis_url: str,
    *,
    decode_responses: bool = True,
    socket_timeout: float = DEFAULT_SOCKET_TIMEOUT,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> redis.Redis:
    return redis.from_url(
        redis_url,
        decode_responses=decode_responses,
        socket_keepalive=True,
        socket_timeout=socket_timeout,
        retry=Retry(
            ExponentialBackoff(cap=2, base=0.1),
            retries=retry_attempts,
            supported_errors=_RECONNECT_ERRORS,
        ),
        retry_on_error=list(_RECONNECT_ERRORS),
    )
