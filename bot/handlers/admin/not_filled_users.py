from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from bot.utils import make_not_filled_message

not_filled_router = Router()


@not_filled_router.message(StateFilter(None), Command("not_filled"))
async def start_custom_handler(msg: Message):
    not_filled_message = await make_not_filled_message()
    await msg.answer(text=not_filled_message)
