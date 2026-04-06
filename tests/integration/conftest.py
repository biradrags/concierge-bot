import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from concierge_bot.dao import HolderDao
from concierge_bot.db.base import Base

DEFAULT_TEST_URL = (
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5437/concierge_bot"
)


@pytest_asyncio.fixture
async def db_engine():
    url = os.environ.get("CONCIERGE_TEST_DATABASE_URL", DEFAULT_TEST_URL)
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except OSError as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL unavailable ({exc})")
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL unavailable ({exc})")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    Session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with Session() as session:
        yield session


@pytest_asyncio.fixture
async def seed_hotel(db_session: AsyncSession):
    holder = HolderDao(db_session)
    h = await holder.hotel.create(
        name="Seed Hotel",
        admin_chat_id=880_001,
        bot_token="seed-token",
    )
    await holder.service.create(
        hotel_id=h.id,
        name="R1",
        category="restaurant",
        is_active=True,
    )
    await holder.service.create(
        hotel_id=h.id,
        name="Mountain Tour",
        category="tour",
        is_active=True,
    )
    await holder.service.create(
        hotel_id=h.id,
        name="Spa active",
        category="spa",
        is_active=True,
    )
    await holder.service.create(
        hotel_id=h.id,
        name="Spa inactive",
        category="spa",
        is_active=False,
    )
    await db_session.commit()
    return h
