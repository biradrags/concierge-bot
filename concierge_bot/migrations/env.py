from logging.config import fileConfig

from alembic import context
from bira_core.db.alembic import run_migrations
from bira_core.db.base import Base
from bira_core.db.settings import ddl_url
from dotenv import find_dotenv, load_dotenv

import concierge_bot.db.models  # noqa: F401
from concierge_bot.config import get_config

load_dotenv(find_dotenv())
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

cfg = get_config()
config.set_main_option("sqlalchemy.url", ddl_url(cfg))

run_migrations(config, Base.metadata, host=cfg.db_host)
