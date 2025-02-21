from aiogram import Router
from aiogram.filters import StateFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.clients.init_clients import storage_client
from bot.states import RemoveUser
from bot.utils import format_users_list
from config import Config

remove_user_router = Router()


@remove_user_router.message(RemoveUser.remove_id)
async def id_inserted(msg: Message, state: FSMContext):
    user_id = msg.text
    if user_name := await storage_client.remove_user(user_id):
        await msg.answer(text=f"{user_name} удален из списка пользователей")
        await state.clear()
    else:
        await msg.answer(text="Ошибка удаления из списка пользователей")


@remove_user_router.message(StateFilter(None), Command("remove_user"))
async def remove_user_handler(msg: Message, command: CommandObject, state: FSMContext):
    if command.args == Config.ADMIN_PHRASE:
        users_list = await format_users_list(await storage_client.get_all_users_list())
        await msg.answer(
            text=f"Введите id того, кого необходимо удалить из напоминаний:\n{users_list}")
        await state.set_state(RemoveUser.remove_id)
