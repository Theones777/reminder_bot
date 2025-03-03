from aiogram import Router
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.clients.init_clients import storage_client
from bot.clients.storage import Storage
from bot.texts import START_ADMIN_MESSAGE, START_USER_MESSAGE, HELP_MESSAGE, MAILING_MESSAGE
from bot.utils import make_inline_keyboard, get_buttons_dict
from config import Config

common_router = Router()


@common_router.message(StateFilter("*"), Command(commands=["start"]))
async def message_start_handler(msg: Message, state: FSMContext):
    await state.set_data({})
    await state.clear()

    user_id: int = msg.from_user.id
    user_full_name: int = msg.from_user.full_name
    tg_user_name: int = msg.from_user.username
    await storage_client.save_new_user(user_id, user_full_name, tg_user_name)
    admin_ids = await Storage.get_admin_ids()

    if user_id in admin_ids:
        message = START_ADMIN_MESSAGE
    else:
        message = START_USER_MESSAGE
    await msg.answer(message, reply_markup=ReplyKeyboardRemove())
    buttons_dict = await get_buttons_dict()
    buttons = buttons_dict.get(user_id)
    if buttons:
        await msg.answer(MAILING_MESSAGE, reply_markup=await make_inline_keyboard(buttons))


@common_router.message(StateFilter("*"), Command("help"))
async def message_help_handler(msg: Message, state: FSMContext):
    await state.set_data({})
    await state.clear()
    await msg.answer(HELP_MESSAGE)


@common_router.message(StateFilter("*"), Command(commands=["cancel"]))
async def cancel_handler(msg: Message, state: FSMContext):
    await state.set_data({})
    await state.clear()
    await msg.answer("Сброс состояния", reply_markup=ReplyKeyboardRemove())


@common_router.message(StateFilter("*"), Command(commands=["register"]))
async def add_admin_handler(msg: Message, command: CommandObject, state: FSMContext):
    if command.args == Config.ADMIN_PHRASE:
        if user_name := await storage_client.add_new_admin(msg.from_user.id):
            await msg.answer(text=f"{user_name} добавлен в список администраторов")
            await state.clear()
