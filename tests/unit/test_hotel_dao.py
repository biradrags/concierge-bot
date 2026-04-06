from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from concierge_bot.dao.hotel import HotelDao
from concierge_bot.db.models import Hotel


@pytest.mark.asyncio
async def test_get_by_admin_chat_id_found(mock_session: MagicMock) -> None:
    hotel = Hotel(
        id=uuid4(),
        name="H",
        admin_chat_id=100,
        forum_chat_id=None,
        bot_token="t",
        max_bot_token=None,
        system_prompt=None,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    scalar_result = MagicMock()
    scalar_result.first.return_value = hotel
    mock_session.scalars = AsyncMock(return_value=scalar_result)

    dao = HotelDao(mock_session)
    dto = await dao.get_by_admin_chat_id(100)

    assert dto is not None
    assert dto.admin_chat_id == 100
    assert dto.name == "H"
    mock_session.scalars.assert_awaited()


@pytest.mark.asyncio
async def test_get_by_admin_chat_id_not_found(mock_session: MagicMock) -> None:
    scalar_result = MagicMock()
    scalar_result.first.return_value = None
    mock_session.scalars = AsyncMock(return_value=scalar_result)

    dao = HotelDao(mock_session)
    dto = await dao.get_by_admin_chat_id(999)

    assert dto is None


@pytest.mark.asyncio
async def test_create_hotel(mock_session: MagicMock) -> None:
    mock_session.flush = AsyncMock()
    dao = HotelDao(mock_session)
    hid = uuid4()
    now = datetime.now(UTC)
    dto = await dao.create(
        id=hid,
        name="New",
        admin_chat_id=55,
        bot_token="tok",
        is_active=True,
        created_at=now,
    )

    assert dto.id == hid
    assert dto.name == "New"
    assert dto.admin_chat_id == 55
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
