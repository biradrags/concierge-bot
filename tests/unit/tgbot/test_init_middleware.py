import ast
import importlib
import pkgutil
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, Update, User
from dishka import Provider, Scope, make_async_container
from dishka.integrations.aiogram import FromDishka, setup_dishka

import concierge_bot.di
import concierge_bot.tgbot
from concierge_bot.dao import HolderDao
from concierge_bot.services.booking import BookingService
from concierge_bot.services.concierge import ConciergeService
from concierge_bot.services.forum import ForumService
from concierge_bot.services.guest import GuestService
from concierge_bot.tgbot.middlewares import setup_middlewares
from concierge_bot.tgbot.middlewares.init import InitMiddleware

KEYS = {
    "dao": HolderDao, "guest_service": GuestService, "booking_service": BookingService,
    "forum": ForumService, "concierge": ConciergeService,
}


async def test_puts_request_dependencies() -> None:
    resolved = {t: object() for t in KEYS.values()}
    container = MagicMock(get=AsyncMock(side_effect=lambda t: resolved[t]))
    seen: dict[str, object] = {}

    async def handler(_event: object, data: dict[str, object]) -> None:
        seen.update(data)

    await InitMiddleware()(handler, object(), {"dishka_container": container})
    assert {key: seen[key] for key in KEYS} == {key: resolved[t] for key, t in KEYS.items()}  # noqa: S101


async def test_handler_gets_update_scope_dao_not_second_scope() -> None:
    """dishka открывает вторую REQUEST-область на observer: хендлер берёт DAO мидлвари апдейта."""
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(_fake_dao, provides=HolderDao)
    for t in KEYS.values():
        if t is not HolderDao:
            provider.provide(lambda: MagicMock(), provides=t)
    container = make_async_container(provider)
    dp = Dispatcher()
    seen: dict[str, object] = {}

    async def handler(_message: Message, dao: HolderDao, other: FromDishka[HolderDao]) -> None:
        seen.update(dao=dao, other=other)

    dp.message.register(handler)
    setup_dishka(container=container, router=dp, auto_inject=True)
    setup_middlewares(dp)
    await dp.emit_startup()  # auto_inject оборачивает хендлеры на старте
    await dp.feed_update(Bot("42:TEST"), _update())
    await container.close()
    dao = seen["dao"]
    assert isinstance(dao, MagicMock)  # noqa: S101
    dao.hotel.get_by_bot_token.assert_awaited_once()  # тот же DAO прочитал ConciergeDataMiddleware
    assert seen["other"] is not dao  # noqa: S101


def test_handlers_take_request_dependencies_from_data() -> None:
    """FromDishka в tgbot - только APP-скоуп; REQUEST берётся из data (dialogs.md)."""
    request = _request_types()
    root = Path(concierge_bot.tgbot.__file__).parent
    hits = []
    for path in root.rglob("*.py"):
        name = ".".join(("concierge_bot", "tgbot", *path.relative_to(root).with_suffix("").parts))
        module = importlib.import_module(name.removesuffix(".__init__"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == "FromDishka"
                and isinstance(node.slice, ast.Name)
                and getattr(module, node.slice.id, None) in request
            ):
                hits.append(f"{path.relative_to(root)}:{node.lineno} {node.slice.id}")
    assert hits == []  # noqa: S101


def _request_types() -> set[object]:
    types: set[object] = set()
    for info in pkgutil.iter_modules(concierge_bot.di.__path__):
        module = importlib.import_module(f"concierge_bot.di.{info.name}")
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, Provider) and obj.__module__ == module.__name__:
                types |= {f.provides.type_hint for f in obj().factories if f.scope is Scope.REQUEST}
    return types


def _fake_dao() -> MagicMock:
    dao = MagicMock()
    dao.hotel.get_by_bot_token = AsyncMock(return_value=None)
    return dao


def _update() -> Update:
    user = User(id=1, is_bot=False, first_name="u")
    message = Message(
        message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private"), from_user=user, text="x"
    )
    return Update(update_id=1, message=message)
