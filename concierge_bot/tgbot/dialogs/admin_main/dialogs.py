from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Group, Row, Start
from aiogram_dialog.widgets.text import Const, Jinja

from concierge_bot.shared.dialogs.admin_main.getters import get_admin_dashboard
from concierge_bot.shared.states import (
    AdminBookingsSG,
    AdminMainSG,
    AdminPromptSG,
    AdminServicesSG,
    AdminStatsSG,
    GuestServicesSG,
)

admin_main_dialog = Dialog(
    Window(
        Jinja(
            "<b>Админ-панель</b>\n"
            "{{ hotel_name }}\n"
            "Ожидают решения: <b>{{ pending_count }}</b>",
        ),
        Group(
            Start(
                Const("🛎 Услуги"),
                id="adm_svc",
                state=AdminServicesSG.list,
            ),
            Start(
                Const("📋 Брони"),
                id="adm_book",
                state=AdminBookingsSG.list,
            ),
            Start(
                Const("🤖 Промпт AI"),
                id="adm_prompt",
                state=AdminPromptSG.view,
            ),
            Start(
                Const("📊 Статистика"),
                id="adm_stats",
                state=AdminStatsSG.main,
            ),
            width=2,
        ),
        Row(
            Start(
                Const("👤 Каталог для гостя"),
                id="guest_cat",
                state=GuestServicesSG.categories,
            ),
        ),
        Row(Cancel(Const("Закрыть"))),
        state=AdminMainSG.main,
        getter=get_admin_dashboard,
    ),
)
