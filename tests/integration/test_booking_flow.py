import pytest

from concierge_bot.dao import HolderDao

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_booking_cycle(db_session, seed_hotel) -> None:
    holder = HolderDao(db_session)
    guest, _ = await holder.guest.get_or_create(
        telegram_user_id=1001,
        hotel_id=seed_hotel.id,
        name="Flow",
        language_code="en",
    )
    await db_session.commit()

    services = await holder.service.get_active_by_hotel(seed_hotel.id)
    assert len(services) >= 1
    svc = services[0]

    booking = await holder.booking.create(
        guest_id=guest.id,
        service_id=svc.id,
        notes="test",
        status="pending",
    )
    await db_session.commit()

    loaded = await holder.booking.get_by_id(booking.id)
    assert loaded is not None
    assert loaded.status == "pending"

    await holder.booking.update_status(booking.id, "confirmed")
    await db_session.commit()

    confirmed = await holder.booking.get_by_id(booking.id)
    assert confirmed is not None
    assert confirmed.status == "confirmed"

    guest_bookings = await holder.booking.get_by_guest(guest.id)
    assert len(guest_bookings) == 1
    assert guest_bookings[0].id == booking.id
