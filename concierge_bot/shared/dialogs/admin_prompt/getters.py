from typing import Any

from aiogram_dialog import DialogManager

from concierge_bot.dto import HotelDTO


async def get_current_prompt(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    hotel: HotelDTO | None = dialog_manager.middleware_data.get("hotel")
    if hotel is None:
        return {"prompt_text": "—"}
    text = hotel.system_prompt or "Системный промпт не задан (по умолчанию из кода агента)."
    return {"prompt_text": text}
