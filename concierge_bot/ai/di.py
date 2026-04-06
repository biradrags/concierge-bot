from agent_framework.openai import OpenAIChatClient
from dishka import Provider, Scope, provide

from concierge_bot.ai.history import (
    ConciergeRedisHistoryProvider,
    build_concierge_history_provider,
)
from concierge_bot.ai.middleware.structured_retry import StructuredOutputRetryMiddleware
from concierge_bot.config import BaseConfig


class AIProvider(Provider):
    scope = Scope.APP

    @provide
    def concierge_history(self, config: BaseConfig) -> ConciergeRedisHistoryProvider:
        return build_concierge_history_provider(config)

    @provide
    def openai_chat_client(self, config: BaseConfig) -> OpenAIChatClient:
        key = (config.openai_api_key or "").strip() or "sk-placeholder"
        return OpenAIChatClient(
            model=config.ai_model,
            api_key=key,
            middleware=[StructuredOutputRetryMiddleware(max_retries=3)],
        )
