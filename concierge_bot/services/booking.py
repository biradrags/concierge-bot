import logging
from uuid import UUID

from aiogram.exceptions import TelegramAPIError

from concierge_bot.dao import HolderDao
from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO
from concierge_bot.services.forum import ForumService
from concierge_bot.services.notification import NotificationService

logger = logging.getLogger(__name__)


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
        # записи -> commit -> отправки (D5): Telegram не держит транзакцию и не врёт при откате
        await self._dao.commit()
        # бронь уже сохранена: сбой уведомления не должен выглядеть для гостя ошибкой брони
        extra = {"booking_id": str(booking.id), "hotel_id": str(hotel.id)}
        try:
            await self._notification.notify_admin(hotel, booking, service, guest)
        except TelegramAPIError:
            logger.warning("admin notification failed", extra=extra, exc_info=True)
        if hotel.forum_chat_id is not None and guest.forum_topic_id is not None:
            try:
                await self._forum.mirror_booking(
                    hotel.forum_chat_id,
                    guest.forum_topic_id,
                    booking,
                    service,
                )
            except TelegramAPIError:
                logger.warning("forum mirror failed", extra=extra, exc_info=True)
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
        if booking.status != "pending":
            return booking  # решение уже принято: ничего не пишем и гостю не шлём
        guest = booking.guest
        if guest is None:
            guest = await self._dao.guest.get_by_id(booking.guest_id)
        if guest is None:
            msg = "Guest not found for booking"
            raise ValueError(msg)
        updated = await self._dao.booking.update_status(booking_id, status)
        await self._dao.commit()  # D5: commit до отправки гостю
        try:
            await self._notification.notify_guest(guest, updated, status)
        except TelegramAPIError:
            logger.warning("guest notification failed", extra={"booking_id": str(booking_id)}, exc_info=True)
        return updated

    async def get_guest_bookings(self, guest_id: UUID) -> list[BookingDTO]:
        return await self._dao.booking.get_by_guest(guest_id)

    async def get_pending_bookings(self, hotel_id: UUID) -> list[BookingDTO]:
        return await self._dao.booking.get_pending_by_hotel(hotel_id)

    async def get_stats(self, hotel_id: UUID) -> dict[str, int]:
        return await self._dao.booking.get_stats_by_hotel(hotel_id)
