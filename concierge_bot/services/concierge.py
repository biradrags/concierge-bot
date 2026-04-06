import asyncio
import logging

from agent_framework.openai import OpenAIChatClient
from aiogram import Bot

from concierge_bot.ai.agents.concierge.agent import run_concierge_agent
from concierge_bot.ai.history import ConciergeRedisHistoryProvider
from concierge_bot.config import BaseConfig
from concierge_bot.dao import HolderDao
from concierge_bot.dto import GuestDTO, HotelDTO
from concierge_bot.services.booking import BookingService
from concierge_bot.services.forum import ForumService

logger = logging.getLogger(__name__)


class ConciergeService:
    def __init__(
        self,
        dao: HolderDao,
        client: OpenAIChatClient,
        history: ConciergeRedisHistoryProvider,
        config: BaseConfig,
        booking_service: BookingService,
        bot: Bot,
        forum: ForumService,
    ) -> None:
        self._dao = dao
        self._client = client
        self._history = history
        self._config = config
        self._booking = booking_service
        self._bot = bot
        self._forum = forum

    async def handle_message(self, hotel: HotelDTO, guest: GuestDTO, text: str) -> str:
        if not (self._config.openai_api_key or "").strip():
            return "Консьерж недоступен: задайте OPENAI_API_KEY в окружении."
        try:
            response = await run_concierge_agent(
                client=self._client,
                config=self._config,
                hotel=hotel,
                guest=guest,
                dao=self._dao,
                booking_service=self._booking,
                bot=self._bot,
                history_provider=self._history,
                user_message=text,
            )
            await self._dao.commit()
            msg = (response.message or "").strip() or "…"
            if hotel.forum_chat_id is not None and guest.forum_topic_id is not None:
                await asyncio.gather(
                    self._forum.mirror_message(hotel.forum_chat_id, guest.forum_topic_id, "Guest", text),
                    self._forum.mirror_message(hotel.forum_chat_id, guest.forum_topic_id, "AI", msg),
                )
            return msg
        except Exception:
            logger.exception("concierge agent failed")
            return "Извините, сейчас не получилось ответить. Попробуйте позже."
