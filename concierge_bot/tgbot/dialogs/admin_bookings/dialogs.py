import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from concierge_bot.shared.dialogs.admin_bookings.getters import (
    get_booking_detail,
    get_pending_bookings,
)
from concierge_bot.shared.dialogs.admin_bookings.handlers import (
    on_cancel_booking,
    on_confirm_booking,
    on_select_booking,
)
from concierge_bot.shared.states import AdminBookingsSG, AdminMainSG

admin_bookings_dialog = Dialog(
    Window(
        Const("<b>Брони (ожидают)</b>"),
        Select(
            Format("{item[label]}"),
            id="bk_sel",
            item_id_getter=operator.itemgetter("id"),
            items="bookings",
            on_click=on_select_booking,
        ),
        Row(SwitchTo(Const("◀️ В админку"), id="b_adm", state=AdminMainSG.main)),
        Row(Cancel(Const("Закрыть"))),
        state=AdminBookingsSG.list,
        getter=get_pending_bookings,
    ),
    Window(
        Jinja("{{ detail_text }}"),
        Row(
            Button(Const("✅ Подтвердить"), id="cfm", on_click=on_confirm_booking),
            Button(Const("❌ Отклонить"), id="cnl", on_click=on_cancel_booking),
        ),
        Row(Back(Const("◀️ К списку"))),
        state=AdminBookingsSG.detail,
        getter=get_booking_detail,
    ),
)
