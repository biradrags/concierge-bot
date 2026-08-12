from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from concierge_bot.dao.base import BaseDAO
from concierge_bot.db.models import Guest, Hotel
from concierge_bot.dto import GuestDTO


class GuestDao(BaseDAO[Guest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Guest, session)

    async def get_by_id(self, guest_id: UUID) -> GuestDTO | None:
        row = await self._get_by_id(guest_id)
        return GuestDTO.model_validate(row) if row else None

    async def get_by_forum_thread(
        self,
        forum_chat_id: int,
        topic_id: int,
    ) -> GuestDTO | None:
        result = await self.session.scalars(
            select(Guest)
            .join(Hotel, Guest.hotel_id == Hotel.id)
            .where(
                Hotel.forum_chat_id == forum_chat_id,
                Guest.forum_topic_id == topic_id,
            ),
        )
        row = result.first()
        return GuestDTO.model_validate(row) if row else None

    async def get_by_telegram_user_id(
        self,
        telegram_user_id: int,
        hotel_id: UUID,
    ) -> GuestDTO | None:
        result = await self.session.scalars(
            select(Guest).where(
                Guest.telegram_user_id == telegram_user_id,
                Guest.hotel_id == hotel_id,
            ),
        )
        row = result.first()
        return GuestDTO.model_validate(row) if row else None

    async def get_or_create(
        self,
        telegram_user_id: int,
        hotel_id: UUID,
        name: str | None,
        language_code: str,
    ) -> tuple[GuestDTO, bool]:
        existing = await self.get_by_telegram_user_id(telegram_user_id, hotel_id)
        if existing:
            return existing, False
        guest = Guest(
            telegram_user_id=telegram_user_id,
            hotel_id=hotel_id,
            name=name,
            language_code=language_code,
        )
        self._save(guest)
        await self._flush()
        return GuestDTO.model_validate(guest), True

    async def update_forum_topic_id(self, guest_id: UUID, topic_id: int | None) -> None:
        guest = await self._get_by_id(guest_id)
        if guest is None:
            msg = f"Guest {guest_id} not found"
            raise ValueError(msg)  # dao-raise-ok: guard when guest id missing in update_forum_topic_id
        guest.forum_topic_id = topic_id
        await self._flush()
