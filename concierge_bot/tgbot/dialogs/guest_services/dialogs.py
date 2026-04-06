import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row, Select
from aiogram_dialog.widgets.text import Const, Format, Jinja

from concierge_bot.shared.dialogs.guest_services.getters import (
    get_booked_done,
    get_categories,
    get_service_detail_guest,
    get_services_by_category,
)
from concierge_bot.shared.dialogs.guest_services.handlers import (
    on_book,
    on_select_category,
    on_select_service,
)
from concierge_bot.shared.states import GuestServicesSG

guest_services_dialog = Dialog(
    Window(
        Const("<b>Услуги отеля</b>\nВыберите категорию:"),
        Select(
            Format("{item[name]}"),
            id="g_cat",
            item_id_getter=operator.itemgetter("id"),
            items="categories",
            on_click=on_select_category,
        ),
        Row(Cancel(Const("Закрыть"))),
        state=GuestServicesSG.categories,
        getter=get_categories,
    ),
    Window(
        Const("Выберите услугу:"),
        Select(
            Format("{item[name]}"),
            id="g_svc",
            item_id_getter=operator.itemgetter("id"),
            items="services",
            on_click=on_select_service,
        ),
        Row(Back(Const("◀️ Категории"))),
        Row(Cancel(Const("Закрыть"))),
        state=GuestServicesSG.list,
        getter=get_services_by_category,
    ),
    Window(
        Jinja("{{ detail }}"),
        Row(Button(Const("📌 Забронировать"), id="book", on_click=on_book)),
        Row(Back(Const("◀️ Назад"))),
        Row(Cancel(Const("Закрыть"))),
        state=GuestServicesSG.detail,
        getter=get_service_detail_guest,
    ),
    Window(
        Jinja("{{ done }}"),
        Row(Cancel(Const("Закрыть"))),
        state=GuestServicesSG.booked,
        getter=get_booked_done,
    ),
)
