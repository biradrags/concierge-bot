import logging
import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

AppEnv = Literal["development", "dev", "production", "prod"]


class BaseConfig(BaseSettings):
    telegram_bot_token: str = Field(default="000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    max_bot_token: str = ""
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5437/concierge_bot",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    openai_api_key: str = ""
    ai_model: str = "gpt-4.1-mini"
    app_env: AppEnv = "development"
    log_level: str = "INFO"
    webhook_host: str = ""
    webhook_secret: str = ""
    webhook_path: str = "/webhook"
    port: int = 8080

    @property
    def webhook_url(self) -> str:
        base = self.webhook_host.rstrip("/")
        if not base:
            return ""
        path = self.webhook_path if self.webhook_path.startswith("/") else f"/{self.webhook_path}"
        return f"{base}{path}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProductionConfig(BaseConfig):
    telegram_bot_token: str = Field(..., min_length=10)
    max_bot_token: str = Field(default="")
    openai_api_key: str = Field(..., min_length=10)
    database_url: str = Field(..., min_length=1)
    redis_url: str = Field(..., min_length=1)
    webhook_host: str = Field(
        default_factory=lambda: f"https://{os.environ.get('FLY_APP_NAME', 'concierge-bot')}.fly.dev",
    )


class DevelopmentConfig(BaseConfig):
    pass


def get_config() -> BaseConfig:
    env = os.environ.get("APP_ENV", "development").lower()
    if env not in ("development", "dev", "production", "prod"):
        env = "development"
    logger.debug("Loading configuration for environment: %s", env)
    mapping: dict[str, type[BaseConfig]] = {
        "production": ProductionConfig,
        "prod": ProductionConfig,
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
    }
    return mapping[env]()
