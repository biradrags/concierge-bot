import logging

from agent_framework.openai import OpenAIChatClient
from aiogram import Bot

from concierge_bot.ai.agents.concierge.context import ConciergeState, ToolDeps
from concierge_bot.ai.agents.concierge.prompts import build_system_prompt
from concierge_bot.ai.agents.concierge.tools import create_booking, search_services
from concierge_bot.ai.contracts import ConciergeResponse
from concierge_bot.ai.factory import create_agent
from concierge_bot.ai.history import ConciergeRedisHistoryProvider
from concierge_bot.ai.middleware import (
    FunctionLoggingMiddleware,
    LoggingMiddleware,
    RetryMiddleware,
    is_retriable_history_error,
)
from concierge_bot.config import BaseConfig
from concierge_bot.dao import HolderDao
from concierge_bot.dto import GuestDTO, HotelDTO
from concierge_bot.services.booking import BookingService

logger = logging.getLogger(__name__)


def create_concierge_agent(
    client: OpenAIChatClient,
    config: BaseConfig,
    hotel: HotelDTO,
    guest: GuestDTO,
    dao: HolderDao,
    booking_service: BookingService,
    bot: Bot,
    history_provider: ConciergeRedisHistoryProvider,
) -> tuple[object, ToolDeps, ConciergeState]:
    deps = ToolDeps(
        hotel=hotel,
        guest=guest,
        dao=dao,
        booking_service=booking_service,
        bot=bot,
    )
    state = ConciergeState()
    middleware = [
        RetryMiddleware(
            retry_if=is_retriable_history_error,
            user_id=guest.telegram_user_id,
        ),
        LoggingMiddleware(),
        FunctionLoggingMiddleware(),
    ]
    agent = create_agent(
        client,
        name="concierge_agent",
        prompt=build_system_prompt(hotel),
        tools=[search_services, create_booking],
        response_format=ConciergeResponse,
        model=config.ai_model,
        middleware=middleware,
        context_providers=[history_provider],
    )
    return agent, deps, state


async def run_concierge_agent(
    client: OpenAIChatClient,
    config: BaseConfig,
    hotel: HotelDTO,
    guest: GuestDTO,
    dao: HolderDao,
    booking_service: BookingService,
    bot: Bot,
    history_provider: ConciergeRedisHistoryProvider,
    user_message: str,
) -> ConciergeResponse:
    agent, deps, state = create_concierge_agent(
        client=client,
        config=config,
        hotel=hotel,
        guest=guest,
        dao=dao,
        booking_service=booking_service,
        bot=bot,
        history_provider=history_provider,
    )
    session_id = f"{hotel.id}:{guest.telegram_user_id}"
    async with agent as a:
        session = a.create_session(session_id=session_id)
        result = await a.run(
            user_message,
            session=session,
            function_invocation_kwargs={"deps": deps, "state": state},
        )
        if result.user_input_requests:
            return ConciergeResponse(
                message="Нужно подтверждение в интерфейсе — отправьте запрос проще или повторите.",
            )
        return result.value
