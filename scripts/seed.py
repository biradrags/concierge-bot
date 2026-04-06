"""Создать демо-отель и услуги. Запуск из корня проекта: uv run python scripts/seed.py"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from concierge_bot.config import get_config
from concierge_bot.dao import HolderDao


async def main() -> None:
    os.environ.setdefault("APP_ENV", "development")
    cfg = get_config()
    engine = create_async_engine(cfg.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        holder = HolderDao(session)
        token = os.environ.get("SEED_BOT_TOKEN", "demo-concierge-token")
        existing = await holder.hotel.get_by_bot_token(token)
        if existing is not None:
            print(f"Отель уже есть: {existing.id} ({existing.name})")
            await engine.dispose()
            return
        h = await holder.hotel.create(
            name=os.environ.get("SEED_HOTEL_NAME", "Demo Concierge Hotel"),
            admin_chat_id=int(os.environ.get("SEED_ADMIN_CHAT_ID", "1000000001")),
            bot_token=token,
            max_bot_token=os.environ.get("SEED_MAX_BOT_TOKEN") or None,
            system_prompt=os.environ.get("SEED_SYSTEM_PROMPT"),
        )
        await holder.service.create(
            hotel_id=h.id,
            name="Ужин в ресторане",
            category="restaurant",
            description="Бронирование столика",
            is_active=True,
        )
        await holder.service.create(
            hotel_id=h.id,
            name="Трансфер",
            category="transport",
            is_active=True,
        )
        await session.commit()
        print(f"Создан отель {h.name} id={h.id}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
