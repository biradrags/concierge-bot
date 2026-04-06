from aiogram.fsm.state import State, StatesGroup


class AdminMainSG(StatesGroup):
    main = State()


class AdminServicesSG(StatesGroup):
    list = State()
    add_name = State()
    add_category = State()
    add_description = State()
    add_price = State()
    confirm = State()
    edit = State()
    delete_confirm = State()


class AdminBookingsSG(StatesGroup):
    list = State()
    detail = State()


class AdminPromptSG(StatesGroup):
    view = State()
    edit = State()


class AdminStatsSG(StatesGroup):
    main = State()


class GuestServicesSG(StatesGroup):
    categories = State()
    list = State()
    detail = State()
    booked = State()
