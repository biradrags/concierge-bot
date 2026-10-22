from datetime import UTC, datetime
from uuid import UUID, uuid4

from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO, ServiceDTO


def make_hotel() -> HotelDTO:
    return HotelDTO(
        id=uuid4(),
        name="H",
        admin_chat_id=1,
        forum_chat_id=None,
        bot_token="t",  # noqa: S106
        max_bot_token=None,
        system_prompt=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )


def make_guest(hotel_id: UUID) -> GuestDTO:
    return GuestDTO(
        id=uuid4(),
        telegram_user_id=777,
        hotel_id=hotel_id,
        name="G",
        language_code="en",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )


def make_service(hotel_id: UUID) -> ServiceDTO:
    return ServiceDTO(
        id=uuid4(),
        hotel_id=hotel_id,
        name="Spa",
        category="spa",
        description=None,
        price=None,
        currency="USD",
        is_active=True,
        created_at=datetime.now(UTC),
    )


def make_booking(guest_id: UUID, service_id: UUID, status: str = "pending") -> BookingDTO:
    return BookingDTO(
        id=uuid4(),
        guest_id=guest_id,
        service_id=service_id,
        status=status,
        notes=None,
        created_at=datetime.now(UTC),
    )
