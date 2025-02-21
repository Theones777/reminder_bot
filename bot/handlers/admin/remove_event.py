from aiogram import Router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.clients.init_clients import storage_client
from bot.states import RemoveEvent
from bot.utils import format_events_list

remove_event_router = Router()


@remove_event_router.message(RemoveEvent.remove_id)
async def id_inserted(msg: Message, state: FSMContext):
    event_id = msg.text
    if event_name := await storage_client.remove_event(event_id):
        await msg.answer(text=f"{event_name} удалено из списка мероприятий")
        await state.clear()
    else:
        await msg.answer(text="Ошибка удаления из списка мероприятий")


@remove_event_router.message(StateFilter(None), Command("remove_event"))
async def remove_event_handler(msg: Message, state: FSMContext):
    events_data = await format_events_list(await storage_client.get_events_list())
    await msg.answer(
        text=f"Введите id мероприятия, которое необходимо удалить:\n{events_data[0]}")
    await state.set_state(RemoveEvent.remove_id)
