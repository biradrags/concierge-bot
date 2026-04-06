from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from concierge_bot.dto import GuestDTO
from concierge_bot.services.guest import GuestService


@pytest.fixture
def mock_holder_dao() -> MagicMock:
    dao = MagicMock()
    dao.guest = MagicMock()
    return dao


@pytest.fixture
def guest_service(mock_holder_dao: MagicMock) -> GuestService:
    return GuestService(mock_holder_dao)


@pytest.mark.asyncio
async def test_get_or_create_new_guest(
    guest_service: GuestService,
    mock_holder_dao: MagicMock,
) -> None:
    hid = uuid4()
    dto = GuestDTO(
        id=uuid4(),
        telegram_user_id=99,
        hotel_id=hid,
        name="N",
        language_code="ru",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )
    mock_holder_dao.guest.get_or_create = AsyncMock(return_value=(dto, True))

    out = await guest_service.get_or_create(99, hid, "N", "ru")

    assert out == dto
    mock_holder_dao.guest.get_or_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_or_create_existing_guest(
    guest_service: GuestService,
    mock_holder_dao: MagicMock,
) -> None:
    hid = uuid4()
    dto = GuestDTO(
        id=uuid4(),
        telegram_user_id=99,
        hotel_id=hid,
        name="N",
        language_code="ru",
        forum_topic_id=None,
        created_at=datetime.now(UTC),
    )
    mock_holder_dao.guest.get_or_create = AsyncMock(return_value=(dto, False))

    out = await guest_service.get_or_create(99, hid, "N", "ru")

    assert out == dto
