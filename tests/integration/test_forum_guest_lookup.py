import pytest

from concierge_bot.dao import HolderDao

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_get_guest_by_forum_thread(db_session) -> None:
    holder = HolderDao(db_session)
    forum_id = -100_123_456_789
    h = await holder.hotel.create(
        name="Forum Hotel",
        admin_chat_id=990_001,
        forum_chat_id=forum_id,
        bot_token="forum-bot",
    )
    g, _ = await holder.guest.get_or_create(
        telegram_user_id=77_777,
        hotel_id=h.id,
        name="T",
        language_code="en",
    )
    await holder.guest.update_forum_topic_id(g.id, 42)
    await db_session.commit()

    found = await holder.guest.get_by_forum_thread(forum_id, 42)
    assert found is not None
    assert found.telegram_user_id == 77_777

    missing = await holder.guest.get_by_forum_thread(forum_id, 99)
    assert missing is None
