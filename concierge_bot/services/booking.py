from uuid import UUID

from concierge_bot.dao import HolderDao
from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO
from concierge_bot.services.forum import ForumService
from concierge_bot.services.notification import NotificationService


class BookingService:
    def __init__(
        self,
        dao: HolderDao,
        notification: NotificationService,
        forum: ForumService,
    ) -> None:
        self._dao = dao
        self._notification = notification
        self._forum = forum

    async def create_booking(
        self,
        guest: GuestDTO,
        service_id: UUID,
        hotel: HotelDTO,
        notes: str | None,
    ) -> BookingDTO:
        service = await self._dao.service.get_by_id(service_id)
        if service is None:
            msg = f"Service {service_id} not found"
            raise ValueError(msg)
        booking = await self._dao.booking.create(
            guest_id=guest.id,
            service_id=service_id,
            notes=notes,
        )
        await self._notification.notify_admin(hotel, booking, service, guest)
        if (
            hotel.forum_chat_id is not None
            and guest.forum_topic_id is not None
        ):
            await self._forum.mirror_booking(
                hotel.forum_chat_id,
                guest.forum_topic_id,
                booking,
                service,
            )
        return booking

    async def confirm_booking(self, booking_id: UUID) -> BookingDTO:
        return await self._update_booking_status(booking_id, "confirmed")

    async def cancel_booking(self, booking_id: UUID) -> BookingDTO:
        return await self._update_booking_status(booking_id, "cancelled")

    async def _update_booking_status(self, booking_id: UUID, status: str) -> BookingDTO:
        booking = await self._dao.booking.get_by_id(booking_id)
        if booking is None:
            msg = f"Booking {booking_id} not found"
            raise ValueError(msg)
        guest = booking.guest
        if guest is None:
            guest = await self._dao.guest.get_by_id(booking.guest_id)
        if guest is None:
            msg = "Guest not found for booking"
            raise ValueError(msg)
        updated = await self._dao.booking.update_status(booking_id, status)
        await self._notification.notify_guest(guest, updated, status)
        return updated

    async def get_guest_bookings(self, guest_id: UUID) -> list[BookingDTO]:
        return await self._dao.booking.get_by_guest(guest_id)

    async def get_pending_bookings(self, hotel_id: UUID) -> list[BookingDTO]:
        return await self._dao.booking.get_pending_by_hotel(hotel_id)

    async def get_stats(self, hotel_id: UUID) -> dict[str, int]:
        return await self._dao.booking.get_stats_by_hotel(hotel_id)
