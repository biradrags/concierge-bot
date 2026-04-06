from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from concierge_bot.shared.dialogs.admin_prompt.getters import get_current_prompt
from concierge_bot.shared.dialogs.admin_prompt.handlers import on_submit_prompt
from concierge_bot.shared.states import AdminMainSG, AdminPromptSG

admin_prompt_dialog = Dialog(
    Window(
        Jinja("<b>Системный промпт</b>\n\n{{ prompt_text }}"),
        Row(
            SwitchTo(Const("✏️ Изменить"), id="to_edit", state=AdminPromptSG.edit),
        ),
        Row(SwitchTo(Const("◀️ В админку"), id="p_adm", state=AdminMainSG.main)),
        Row(Cancel(Const("Закрыть"))),
        state=AdminPromptSG.view,
        getter=get_current_prompt,
    ),
    Window(
        Const("Отправьте новый текст промпта одним сообщением:"),
        TextInput(id="prompt_body", on_success=on_submit_prompt),
        Row(Back(Const("◀️ Назад"))),
        state=AdminPromptSG.edit,
    ),
)
