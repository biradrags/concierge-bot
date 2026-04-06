from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import FromDishka, inject

from concierge_bot.dao import HolderDao
from concierge_bot.shared.states import AdminMainSG

router = Router(name="admin")


@router.message(Command("admin"))
@inject
async def cmd_admin(
    message: Message,
    dialog_manager: DialogManager,
    bot: FromDishka[Bot],
    dao: FromDishka[HolderDao],
) -> None:
    if message.chat.type != "private":
        await message.answer("Команда доступна в личном чате с ботом.")
        return
    hotel = await dao.hotel.get_by_bot_token(bot.token)
    if hotel is None:
        await message.answer("Отель не найден по токену бота.")
        return
    if message.chat.id != hotel.admin_chat_id:
        await message.answer("Нет доступа к админ-панели.")
        return
    await dialog_manager.start(AdminMainSG.main, mode=StartMode.RESET_STACK)
