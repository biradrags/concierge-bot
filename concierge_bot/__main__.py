import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from dishka.integrations.aiohttp import FromDishka, inject, setup_dishka

from concierge_bot.config import BaseConfig, get_config
from concierge_bot.main_factory import create_dishka
from concierge_bot.tgbot.main_factory import resolve_update_types
from concierge_bot.utils.logging import setup_logging

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


@routes.post("/webhook")
@inject
async def telegram_webhook(
    request: web.Request,
    handler: FromDishka[SimpleRequestHandler],
) -> web.Response:
    return await handler.handle(request)


@inject
async def _on_startup(
    app: web.Application,
    bot: FromDishka[Bot],
    dp: FromDishka[Dispatcher],
    config: FromDishka[BaseConfig],
) -> None:
    workflow_data = {"app": app, "dispatcher": dp, "bot": bot, **dp.workflow_data}
    await dp.emit_startup(**workflow_data)
    if config.webhook_url:
        secret = config.webhook_secret.strip() or None
        await bot.set_webhook(
            url=config.webhook_url,
            secret_token=secret,
            allowed_updates=resolve_update_types(dp),
        )
        logger.info("Webhook set to %s", config.webhook_url)
    else:
        logger.warning("webhook_url пуст — для dev: python -m concierge_bot.tgbot")


@inject
async def _on_shutdown(
    app: web.Application,
    bot: FromDishka[Bot],
    dp: FromDishka[Dispatcher],
) -> None:
    workflow_data = {"app": app, "dispatcher": dp, "bot": bot, **dp.workflow_data}
    await dp.emit_shutdown(**workflow_data)
    await bot.delete_webhook(drop_pending_updates=False)


def main() -> None:
    cfg = get_config()
    setup_logging(cfg.log_level)
    container = create_dishka()
    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(_on_startup)
    app.on_shutdown.append(_on_shutdown)
    setup_dishka(container, app, auto_inject=True)
    web.run_app(app, host="0.0.0.0", port=cfg.port)  # noqa: S104


if __name__ == "__main__":
    main()
