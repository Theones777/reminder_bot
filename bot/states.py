from aiogram.fsm.state import StatesGroup, State


class RemoveEvent(StatesGroup):
    remove_id = State()


class RemoveUser(StatesGroup):
    remove_id = State()


class RemoveAdmin(StatesGroup):
    remove_id = State()


class AddAdmin(StatesGroup):
    add_id = State()


class Sync(StatesGroup):
    event = State()


class User(StatesGroup):
    input = State()
    confirm = State()
