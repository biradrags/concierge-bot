import pytest

from concierge_bot.dao import HolderDao

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_get_active_services_by_hotel(db_session, seed_hotel) -> None:  # noqa: ANN001
    holder = HolderDao(db_session)
    active = await holder.service.get_active_by_hotel(seed_hotel.id)
    names = {s.name for s in active}
    assert "R1" in names  # noqa: S101
    assert "Mountain Tour" in names  # noqa: S101
    assert "Spa active" in names  # noqa: S101
    assert "Spa inactive" not in names  # noqa: S101
    assert len(active) == 3  # noqa: S101


@pytest.mark.asyncio
async def test_search_services(db_session, seed_hotel) -> None:  # noqa: ANN001
    holder = HolderDao(db_session)
    hits = await holder.service.search(seed_hotel.id, "Mountain")
    assert len(hits) == 1  # noqa: S101
    assert hits[0].name == "Mountain Tour"  # noqa: S101


@pytest.mark.asyncio
async def test_booking_stats(db_session, seed_hotel) -> None:  # noqa: ANN001
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
    assert stats.get("pending") == 2  # noqa: S101
    assert stats.get("confirmed") == 1  # noqa: S101
