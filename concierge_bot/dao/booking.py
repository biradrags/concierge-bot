from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from concierge_bot.dao.base import BaseDAO
from concierge_bot.db.models import Booking, Guest
from concierge_bot.dto import BookingDTO


def _booking_shallow(booking: Booking) -> BookingDTO:
    return BookingDTO(
        id=booking.id,
        guest_id=booking.guest_id,
        service_id=booking.service_id,
        status=booking.status,
        notes=booking.notes,
        created_at=booking.created_at,
    )


class BookingDao(BaseDAO[Booking]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Booking, session)

    async def create(
        self,
        guest_id: UUID,
        service_id: UUID,
        notes: str | None = None,
        status: str = "pending",
    ) -> BookingDTO:
        booking = Booking(
            guest_id=guest_id,
            service_id=service_id,
            notes=notes,
            status=status,
        )
        self._save(booking)
        await self._flush()
        return _booking_shallow(booking)

    async def get_by_id(self, booking_id: UUID) -> BookingDTO | None:
        result = await self.session.scalars(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                joinedload(Booking.service),
                joinedload(Booking.guest),
            ),
        )
        row = result.first()
        if row is None:
            return None
        return BookingDTO.model_validate(row)

    async def get_by_guest(self, guest_id: UUID) -> list[BookingDTO]:
        result = await self.session.scalars(
            select(Booking)
            .where(Booking.guest_id == guest_id)
            .options(
                joinedload(Booking.service),
                joinedload(Booking.guest),
            ),
        )
        return [BookingDTO.model_validate(r) for r in result.all()]

    async def get_pending_by_hotel(self, hotel_id: UUID) -> list[BookingDTO]:
        result = await self.session.scalars(
            select(Booking)
            .join(Guest, Booking.guest_id == Guest.id)
            .where(
                Guest.hotel_id == hotel_id,
                Booking.status == "pending",
            )
            .options(
                joinedload(Booking.service),
                joinedload(Booking.guest),
            ),
        )
        return [BookingDTO.model_validate(r) for r in result.all()]

    async def update_status(self, booking_id: UUID, status: str) -> BookingDTO:
        booking = await self._get_by_id(booking_id)
        if booking is None:
            msg = f"Booking {booking_id} not found"
            raise ValueError(msg)
        booking.status = status
        await self._flush()
        return _booking_shallow(booking)

    async def get_stats_by_hotel(self, hotel_id: UUID) -> dict[str, int]:
        stmt = (
            select(Booking.status, func.count(Booking.id))
            .join(Guest, Booking.guest_id == Guest.id)
            .where(Guest.hotel_id == hotel_id)
            .group_by(Booking.status)
        )
        rows = (await self.session.execute(stmt)).all()
        return {status: int(cnt) for status, cnt in rows}
