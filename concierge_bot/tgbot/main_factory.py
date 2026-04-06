from aiogram import Dispatcher


def resolve_update_types(dp: Dispatcher) -> list[str]:
    return dp.resolve_used_update_types()
