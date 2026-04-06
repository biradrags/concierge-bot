from maxo import Bot as MaxBot
from maxo import Router
from maxo.enums import TextFormat
from maxo.routing.ctx import Ctx
from maxo.routing.updates.bot_started import BotStarted

WELCOME = (
    "<b>Консьерж отеля</b>\n"
    "Задайте вопрос текстом — ответит AI-ассистент.\n"
    "Команды: /mybookings — ваши брони; /admin — управление в Telegram."
)


async def on_bot_started(update: BotStarted, ctx: Ctx) -> None:
    bot: MaxBot = ctx["bot"]
    await bot.send_message(
        user_id=update.user.user_id,
        text=WELCOME,
        format=TextFormat.HTML,
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.bot_started.handler(on_bot_started)
    return router
