from uuid import UUID

from concierge_bot.dao import HolderDao
from concierge_bot.dto import GuestDTO


class GuestService:
    def __init__(self, dao: HolderDao) -> None:
        self._dao = dao

    async def get_or_create(
        self,
        telegram_user_id: int,
        hotel_id: UUID,
        name: str | None,
        language_code: str,
    ) -> GuestDTO:
        dto, _created = await self._dao.guest.get_or_create(
            telegram_user_id=telegram_user_id,
            hotel_id=hotel_id,
            name=name,
            language_code=language_code,
        )
        return dto
