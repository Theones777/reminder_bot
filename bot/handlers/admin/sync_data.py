from aiogram import Router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.clients.init_clients import storage_client
from bot.states import Sync
from bot.utils import sync_db_to_gs, format_events_list

sync_router = Router()


@sync_router.message(Sync.event)
async def event_chosen(msg: Message, state: FSMContext):
    event_id = msg.text
    if await sync_db_to_gs(event_id):
        message = "Синхронизация базы данных с Гугл-таблицей завершена"
    else:
        message = "Ошибка синхронизации"
    await msg.answer(text=message)
    await state.clear()


@sync_router.message(StateFilter(None), Command("sync"))
async def sync_handler(msg: Message, state: FSMContext):
    events_data = await format_events_list(await storage_client.get_events_list())
    await msg.answer(
        text=f"Введите id мероприятия, которое необходимо синхронизировать:\n{events_data[0]}")
    await state.update_data(events_info=events_data[1])
    await state.set_state(Sync.event)
