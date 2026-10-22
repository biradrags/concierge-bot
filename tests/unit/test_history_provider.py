from concierge_bot.ai.history import build_concierge_history_provider
from concierge_bot.config import BaseConfig


def test_build_concierge_history_provider_sets_application_id() -> None:
    config = BaseConfig(redis_url="redis://localhost:6379/0")
    provider = build_concierge_history_provider(config)
    assert provider.application_id == "concierge"  # noqa: S101
