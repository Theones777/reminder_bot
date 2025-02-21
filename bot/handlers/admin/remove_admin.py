from aiogram import Router
from aiogram.filters import StateFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.clients.init_clients import storage_client
from bot.states import RemoveAdmin
from bot.utils import format_users_list
from config import Config

remove_admin_router = Router()


@remove_admin_router.message(RemoveAdmin.remove_id)
async def id_inserted(msg: Message, state: FSMContext):
    user_id = msg.text
    if user_name := await storage_client.remove_admin(user_id):
        await msg.answer(text=f"{user_name} удален из списка администраторов")
        await state.clear()
    else:
        await msg.answer(text="Ошибка удаления из списка администраторов")


@remove_admin_router.message(StateFilter(None), Command("remove_admin"))
async def remove_admin_handler(msg: Message, command: CommandObject, state: FSMContext):
    if command.args == Config.ADMIN_PHRASE:
        admins_list = await format_users_list(await storage_client.get_admins_list())
        await msg.answer(
            text=f"Введите id того, у кого необходимо забрать права администратора:\n{admins_list}")
        await state.set_state(RemoveAdmin.remove_id)
