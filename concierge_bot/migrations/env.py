import asyncio
from logging.config import fileConfig

from alembic import context
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import concierge_bot.db.models  # noqa: F401
from concierge_bot.config import get_config
from concierge_bot.db.base import Base

load_dotenv(find_dotenv())
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

cfg = get_config()
config.set_main_option("sqlalchemy.url", str(cfg.database_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"ssl": False},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_sync() -> None:
    from sqlalchemy import create_engine

    url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(url, poolclass=pool.NullPool)

    with engine.connect() as connection:
        do_run_migrations(connection)

    engine.dispose()


def run_migrations_online() -> None:
    url = config.get_main_option("sqlalchemy.url")
    if url and "+asyncpg" not in url:
        run_migrations_sync()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
