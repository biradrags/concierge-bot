from logging.config import fileConfig

from alembic import context
from bira_core.db.alembic import run_migrations
from dotenv import find_dotenv, load_dotenv
from sqlalchemy.engine import make_url

import concierge_bot.db.models  # noqa: F401
from concierge_bot.config import get_config
from concierge_bot.db.base import Base

load_dotenv(find_dotenv())
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

cfg = get_config()
config.set_main_option("sqlalchemy.url", str(cfg.database_url))

run_migrations(
    config,
    Base.metadata,
    host=make_url(str(cfg.database_url)).host or "",
)
