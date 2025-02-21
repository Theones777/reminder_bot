from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.clients.init_clients import storage_client
from bot.states import User
from bot.utils import (
    make_inline_keyboard,
    UserConfirmButtons, format_user_input,
)
from config import Config

user_router = Router()


@user_router.callback_query(User.confirm, F.data.in_([el.name for el in UserConfirmButtons]))
async def confirm(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    if callback.data == UserConfirmButtons.sure.name:
        user_event_data = user_data.get("user_event_data")
        event_callback_data = user_data.get("event_callback_data")
        if not await storage_client.save_filled_data(callback.from_user.id, user_event_data, event_callback_data):
            message = "Ошибка передачи данных, пожалуйста свяжитесь с администратором"
        else:
            message = "Спасибо за предоставление информации"
    else:
        message = "Внесение информации отменено"

    await state.set_data({})
    await state.clear()
    await callback.message.answer(text=message)
    await callback.answer()


@user_router.message(User.input)
async def data_inserted(msg: Message, state: FSMContext):
    user_input = msg.text
    keyboard = None
    user_data = await state.get_data()
    if Config.SEPARATOR in user_input:
        message = f"В введенном тексте есть <b>{Config.SEPARATOR}</b>\nПожалуйста замените этот символ на другой"
    else:
        steps_info = user_data.get("steps_info")
        step = user_data.get("step", 1)
        user_input_saved = user_data.get("user_event_data", "")
        if step == len(steps_info):
            full_user_event_data = user_input_saved + user_input
            event_data = await format_user_input(full_user_event_data, steps_info)
            message = f"Вы уверены, что хотите отправить данную информацию?\n\n{event_data}"
            await state.update_data(user_event_data=full_user_event_data)
            keyboard = await make_inline_keyboard([{
                "text": button.value,
                "callback_data": button.name
            } for button in UserConfirmButtons])
            await state.set_state(User.confirm)
        else:
            await state.set_state(User.input)
            message = f"Введите пожалуйста {steps_info[step]}"
            await state.update_data(
                {
                    "step": step + 1,
                    "user_event_data": user_input_saved + user_input + Config.SEPARATOR,
                }
            )
    await msg.answer(text=message, reply_markup=keyboard)


@user_router.callback_query(
    StateFilter(None),
    lambda callback: callback.data not in [el.name for el in UserConfirmButtons]
)
async def message_handler(callback: CallbackQuery, state: FSMContext):
    callback_data = callback.data

    if event := await storage_client.get_event_with_callback_data(callback_data):
        steps_info = [el.strip() for el in event.event_info.split(",")]
        await state.update_data(
            {
                "steps_info":steps_info,
                "event_callback_data":callback_data,
            }
        )

        await state.set_state(User.input)

        await callback.message.answer(text=f"Введите пожалуйста {steps_info[0]}")
        await callback.answer()
    else:
        await callback.answer("Невозможно предоставить данные по этому мероприятию")
