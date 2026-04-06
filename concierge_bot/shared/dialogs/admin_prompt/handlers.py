from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput

from concierge_bot.dao import HolderDao
from concierge_bot.dto import HotelDTO
from concierge_bot.shared.states import AdminPromptSG


async def on_submit_prompt(
    m: Message,
    _: ManagedTextInput[str],
    manager: DialogManager,
    __: str,
) -> None:
    dao: HolderDao = manager.middleware_data["dao"]
    hotel: HotelDTO | None = manager.middleware_data.get("hotel")
    if not hotel:
        await manager.switch_to(AdminPromptSG.view)
        return
    text = (m.text or "").strip()
    await dao.hotel.update(hotel.id, system_prompt=text or None)
    await dao.commit()
    await manager.switch_to(AdminPromptSG.view)
