import pytest
from sqlalchemy.exc import IntegrityError

from concierge_bot.dao import HolderDao
from concierge_bot.db.models import Guest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_same_user_different_hotels(db_session) -> None:  # noqa: ANN001
    holder = HolderDao(db_session)
    h1 = await holder.hotel.create(
        name="H1",
        admin_chat_id=770_001,
        bot_token="t1",  # noqa: S106
    )
    h2 = await holder.hotel.create(
        name="H2",
        admin_chat_id=770_002,
        bot_token="t2",  # noqa: S106
    )
    await db_session.commit()

    await holder.guest.get_or_create(5000, h1.id, None, "en")
    await holder.guest.get_or_create(5000, h2.id, None, "en")
    await db_session.commit()


@pytest.mark.asyncio
async def test_same_user_same_hotel(db_session) -> None:  # noqa: ANN001
    holder = HolderDao(db_session)
    h = await holder.hotel.create(
        name="H",
        admin_chat_id=770_010,
        bot_token="tx",  # noqa: S106
    )
    await db_session.commit()

    await holder.guest.get_or_create(6000, h.id, None, "en")
    await db_session.commit()

    dup = Guest(
        telegram_user_id=6000,
        hotel_id=h.id,
        name=None,
        language_code="en",
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        await db_session.flush()
