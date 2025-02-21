from aiogram import Router
from aiogram.filters import StateFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.clients.init_clients import storage_client
from bot.states import AddAdmin
from bot.utils import format_users_list
from config import Config

add_admin_router = Router()


@add_admin_router.message(AddAdmin.add_id)
async def custom_type_chosen(msg: Message, state: FSMContext):
    user_id = msg.text
    if user_name := await storage_client.add_new_admin(user_id):
        await msg.answer(text=f"{user_name} добавлен в список администраторов")
        await state.clear()
    else:
        await msg.answer(text="Ошибка добавления в список администраторов")


@add_admin_router.message(StateFilter(None), Command("add_admin"))
async def add_admin_handler(msg: Message, command: CommandObject, state: FSMContext):
    if command.args == Config.ADMIN_PHRASE:
        users_list = await format_users_list(await storage_client.get_all_users_list())
        await msg.answer(
            text=f"Введите id того, кому необходимо выдать права администратора:\n{users_list}")
        await state.set_state(AddAdmin.add_id)
