from sqlalchemy.ext.asyncio import AsyncSession

from concierge_bot.dao.booking import BookingDao
from concierge_bot.dao.guest import GuestDao
from concierge_bot.dao.hotel import HotelDao
from concierge_bot.dao.service import ServiceDao


class HolderDao:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.hotel = HotelDao(session)
        self.service = ServiceDao(session)
        self.guest = GuestDao(session)
        self.booking = BookingDao(session)

    async def commit(self) -> None:
        await self.session.commit()
