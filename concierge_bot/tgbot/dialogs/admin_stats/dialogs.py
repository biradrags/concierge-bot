from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from concierge_bot.shared.dialogs.admin_stats.getters import get_booking_stats
from concierge_bot.shared.states import AdminMainSG, AdminStatsSG

admin_stats_dialog = Dialog(
    Window(
        Jinja("<b>Статистика броней</b>\n\n<pre>{{ stats_text }}</pre>"),
        Row(SwitchTo(Const("◀️ В админку"), id="st_adm", state=AdminMainSG.main)),
        Row(Cancel(Const("Закрыть"))),
        state=AdminStatsSG.main,
        getter=get_booking_stats,
    ),
)
