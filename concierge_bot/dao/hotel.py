from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from concierge_bot.dao.base import BaseDAO
from concierge_bot.db.models import Hotel
from concierge_bot.dto import HotelDTO


class HotelDao(BaseDAO[Hotel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Hotel, session)

    async def get_by_id(self, hotel_id: UUID) -> HotelDTO | None:
        row = await self._get_by_id(hotel_id)
        return HotelDTO.model_validate(row) if row else None

    async def get_by_admin_chat_id(self, chat_id: int) -> HotelDTO | None:
        result = await self.session.scalars(
            select(Hotel).where(Hotel.admin_chat_id == chat_id),
        )
        row = result.first()
        return HotelDTO.model_validate(row) if row else None

    async def get_by_bot_token(self, token: str) -> HotelDTO | None:
        result = await self.session.scalars(
            select(Hotel).where(Hotel.bot_token == token),
        )
        row = result.first()
        return HotelDTO.model_validate(row) if row else None

    async def get_by_forum_chat_id(self, forum_chat_id: int) -> HotelDTO | None:
        result = await self.session.scalars(
            select(Hotel).where(Hotel.forum_chat_id == forum_chat_id),
        )
        row = result.first()
        return HotelDTO.model_validate(row) if row else None

    async def get_by_max_bot_token(self, token: str) -> HotelDTO | None:
        result = await self.session.scalars(
            select(Hotel).where(Hotel.max_bot_token == token),
        )
        row = result.first()
        return HotelDTO.model_validate(row) if row else None

    async def create(self, **kwargs: object) -> HotelDTO:
        hotel = Hotel(**kwargs)  # type: ignore[arg-type]
        self._save(hotel)
        await self._flush()
        return HotelDTO.model_validate(hotel)

    async def update(self, hotel_id: UUID, **kwargs: object) -> HotelDTO:
        hotel = await self._get_by_id(hotel_id)
        if hotel is None:
            msg = f"Hotel {hotel_id} not found"
            raise ValueError(msg)  # dao-raise-ok: guard when hotel id missing in update
        for k, v in kwargs.items():
            setattr(hotel, k, v)
        await self._flush()
        return HotelDTO.model_validate(hotel)
