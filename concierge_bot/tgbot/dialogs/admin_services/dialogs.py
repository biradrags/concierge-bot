import operator

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja

from concierge_bot.shared.dialogs.admin_services.getters import (
    get_add_summary,
    get_categories,
    get_service_detail,
    get_services_list,
)
from concierge_bot.shared.dialogs.admin_services.handlers import (
    on_add_description,
    on_add_name,
    on_add_price,
    on_confirm_add,
    on_delete_service,
    on_pick_category,
    on_select_service,
)
from concierge_bot.shared.states import AdminMainSG, AdminServicesSG

admin_services_dialog = Dialog(
    Window(
        Const("<b>Услуги</b>"),
        Select(
            Format("{item[name]}"),
            id="svc_sel",
            item_id_getter=operator.itemgetter("id"),
            items="services",
            on_click=on_select_service,
        ),
        Row(
            SwitchTo(Const("➕ Добавить"), id="add", state=AdminServicesSG.add_name),
        ),
        Row(SwitchTo(Const("◀️ В админку"), id="back_adm", state=AdminMainSG.main)),
        Row(Cancel(Const("Закрыть"))),
        state=AdminServicesSG.list,
        getter=get_services_list,
    ),
    Window(
        Const("Название услуги (текстом):"),
        TextInput(id="svc_name", on_success=on_add_name),
        Row(SwitchTo(Const("◀️ Отмена"), id="x", state=AdminServicesSG.list)),
        state=AdminServicesSG.add_name,
    ),
    Window(
        Const("Категория:"),
        Select(
            Format("{item[name]}"),
            id="cat_sel",
            item_id_getter=operator.itemgetter("id"),
            items="categories",
            on_click=on_pick_category,
        ),
        Row(Back(Const("◀️ Назад"))),
        state=AdminServicesSG.add_category,
        getter=get_categories,
    ),
    Window(
        Const("Описание (или отправьте «-» чтобы пропустить):"),
        TextInput(id="svc_desc", on_success=on_add_description),
        Row(Back(Const("◀️ Назад"))),
        state=AdminServicesSG.add_description,
    ),
    Window(
        Const("Цена в USD (число или «-»):"),
        TextInput(id="svc_price", on_success=on_add_price),
        Row(Back(Const("◀️ Назад"))),
        state=AdminServicesSG.add_price,
    ),
    Window(
        Jinja("<b>Проверка</b>\n<pre>{{ summary }}</pre>"),
        Row(Button(Const("✅ Создать"), id="do_create", on_click=on_confirm_add)),
        Row(Back(Const("◀️ Назад"))),
        state=AdminServicesSG.confirm,
        getter=get_add_summary,
    ),
    Window(
        Jinja("{{ detail }}"),
        Row(
            SwitchTo(Const("◀️ К списку"), id="to_list", state=AdminServicesSG.list),
        ),
        Row(Button(Const("🗑 Удалить"), id="del_svc", on_click=on_delete_service)),
        state=AdminServicesSG.edit,
        getter=get_service_detail,
    ),
)
