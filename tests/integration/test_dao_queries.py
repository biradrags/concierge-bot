import pytest

from concierge_bot.dao import HolderDao

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_get_active_services_by_hotel(db_session, seed_hotel) -> None:
    holder = HolderDao(db_session)
    active = await holder.service.get_active_by_hotel(seed_hotel.id)
    names = {s.name for s in active}
    assert "R1" in names
    assert "Mountain Tour" in names
    assert "Spa active" in names
    assert "Spa inactive" not in names
    assert len(active) == 3


@pytest.mark.asyncio
async def test_search_services(db_session, seed_hotel) -> None:
    holder = HolderDao(db_session)
    hits = await holder.service.search(seed_hotel.id, "Mountain")
    assert len(hits) == 1
    assert hits[0].name == "Mountain Tour"


@pytest.mark.asyncio
async def test_booking_stats(db_session, seed_hotel) -> None:
    holder = HolderDao(db_session)
    guest, _ = await holder.guest.get_or_create(
        telegram_user_id=2002,
        hotel_id=seed_hotel.id,
        name="S",
        language_code="en",
    )
    services = await holder.service.get_active_by_hotel(seed_hotel.id)
    s0, s1 = services[0], services[1]

    await holder.booking.create(guest_id=guest.id, service_id=s0.id, status="pending")
    await holder.booking.create(guest_id=guest.id, service_id=s1.id, status="pending")
    await holder.booking.create(guest_id=guest.id, service_id=s0.id, status="confirmed")
    await db_session.commit()

    stats = await holder.booking.get_stats_by_hotel(seed_hotel.id)
    assert stats.get("pending") == 2
    assert stats.get("confirmed") == 1
