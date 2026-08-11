"""Guard: FSM storage must survive Fly restarts (RedisStorage, not MemoryStorage).

Статический guard-тест на исходник провайдера - дешевле, чем поднимать DI-контейнер
(паттерн solodki-bot).
"""

import inspect

import concierge_bot.di.tg_provider as m


def test_fsm_storage_is_redis() -> None:
    src = inspect.getsource(m)
    assert "MemoryStorage" not in src, "FSM must survive Fly restarts: use RedisStorage"  # noqa: S101
    assert "RedisStorage" in src  # noqa: S101
