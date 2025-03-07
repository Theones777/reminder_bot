import asyncio
import traceback
from datetime import datetime, time, timedelta
from enum import Enum

import pandas as pd
from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.clients.init_clients import storage_client, gs_client
from bot.log import logger
from bot.texts import MAILING_MESSAGE
from config import Config


class UserConfirmButtons(Enum):
    sure = "Уверен"
    cancel = "Отмена"


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Внести данные"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="cancel", description="Отмена"),
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def make_inline_keyboard(buttons_info: list) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for button_info in buttons_info:
        builder.add(
            InlineKeyboardButton(
                text=f"{button_info.get("text")}",
                callback_data=button_info.get("callback_data")
            )
        )
    return builder.as_markup()


async def format_user_input(user_event_data: str, steps_info: list):
    result = ""
    user_event_data_list = [el.strip() for el in user_event_data.split(Config.SEPARATOR)]
    for i, el in enumerate(steps_info):
        result += f"{el} - {user_event_data_list[i]}\n"
    return result


async def get_events_info_dict(events_info: list) -> dict:
    events_info_dict= {}
    for event_info in events_info:
        event_name, event_callback_data, event_date = event_info
        events_info_dict[event_name] = [event_callback_data, event_date]

    return events_info_dict


async def get_filled_events_dict(filled_events: list) -> dict:
    filled_events_dict = {}
    if filled_events:
        for filled_info in filled_events:
            tg_id, event_name, event_date = filled_info
            if tg_id in filled_events_dict:
                filled_events_dict[tg_id].append(f"{event_name}_{event_date}")
            else:
                filled_events_dict[tg_id] = [f"{event_name}_{event_date}"]

    return filled_events_dict


async def make_buttons_dict(filled_events: list, all_users_list: list, events_info: list) -> dict:
    events_info_dict = await get_events_info_dict(events_info)
    filled_events_dict = await get_filled_events_dict(filled_events)
    buttons_dict = {}

    for user_info in all_users_list:
        user_id = user_info[0]
        buttons_dict[user_id] = []
        if user_id not in filled_events_dict:
            for event_name, (event_callback_data, event_date) in events_info_dict.items():
                buttons_dict[user_id].append(
                    {
                        "text": event_name,
                        "callback_data": event_callback_data,
                    }
                )
        else:
            for event_name, (event_callback_data, event_date) in events_info_dict.items():
                if f"{event_name}_{event_date}" not in filled_events_dict[user_id]:
                    buttons_dict[user_id].append(
                        {
                            "text": event_name,
                            "callback_data": event_callback_data,
                        }
                    )
        if not buttons_dict[user_id]:
            del buttons_dict[user_id]
    return buttons_dict


async def get_buttons_dict():

    all_users_list = await storage_client.get_all_users_list()
    filled_events = await storage_client.get_filled_events()
    events_info = await storage_client.get_remind_events_info()
    buttons_dict = await make_buttons_dict(filled_events, all_users_list, events_info)

    return buttons_dict


async def create_user_mailing_message(buttons: list) -> str:
    message = MAILING_MESSAGE
    for button in buttons:
        event = await storage_client.get_event_with_callback_data(button.get("callback_data"))
        if event.term_date:
            message += f"\n<u>{button.get("text")}</u> - <b>{event.term_date}</b>"
    return message


async def mailing(bot: Bot):
    await storage_client.update_events(await gs_client.get_all_events())
    buttons_dict = await get_buttons_dict()

    for user_id in buttons_dict.keys():
        buttons = buttons_dict[user_id]
        mailing_message = await create_user_mailing_message(buttons)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=mailing_message,
                reply_markup=await make_inline_keyboard(buttons),
            )
        except Exception as e:
            logger.error(f"Ошибка рассылки для {user_id}: {e}")


async def remind(bot: Bot):
    while True:
        now = datetime.now()
        target_time = time(Config.REMIND_TIME, 0)

        if now.time() > target_time:
            next_run = datetime.combine(now.date(), target_time) + timedelta(days=1)
        else:
            next_run = datetime.combine(now.date(), target_time)

        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        await mailing(bot)
        logger.info("Make remind mailing")


async def format_users_list(users_list: list) -> str:
    result = "id - Имя пользователя\n"
    for user_info in users_list:
        result += f"{user_info[0]} - {user_info[1]}/{user_info[2]}\n"
    return result


async def format_events_list(events_list: list) -> str:
    result = "id - Название - Дата\n"
    events_dict = {}

    for event_info in events_list:
        event_id = event_info[0]
        result += f"{event_id} - {event_info[1]} - {event_info[2]}\n"
        events_dict[event_id] = event_info[3]
    return result, events_dict


async def make_not_filled_message():
    result = ""
    all_users_list = await storage_client.get_all_users_list()
    filled_events = await storage_client.get_filled_events()
    events_info = await storage_client.get_remind_events_info()

    events_info_dict = await get_events_info_dict(events_info)
    filled_events_dict = await get_filled_events_dict(filled_events)

    for user_info in all_users_list:
        user_id = user_info[0]
        user_str = ""
        if user_id not in filled_events_dict:
            for event_name, event_data in events_info_dict.items():
                event_callback_data, event_date = event_data
                user_str += f"{event_name}_{event_date}, "
        else:
            for event_name, event_data in events_info_dict.items():
                event_callback_data, event_date = event_data
                if f"{event_name}_{event_date}" not in filled_events_dict[user_id]:
                    user_str += f"{event_name}_{event_date}, "
        if user_str:
            user_name = await storage_client.get_user_name(user_id)
            user_str = f"{user_name} - {user_str}"
            result += f"{user_str}\n\n"

    if not result:
        result = "все данные заполнены"

    return result


async def sync_db_to_gs(event_id: int):
    df_dict = {}
    try:
        db_events_data = await storage_client.get_sync_filled_events(event_id)
        event_name, event_date, event_info = db_events_data[0]
        filled_events_data = db_events_data[1]
        page_name = f"{event_name}_{event_date}"
        columns = [col_name.strip() for col_name in event_info.split(",")]
        for col in columns:
            df_dict[col] = []
        for user_input_raw in filled_events_data:
            user_input = [el.strip() for el in user_input_raw.split(Config.SEPARATOR)]
            for i, data in enumerate(user_input):
                df_dict[columns[i]].append(data)
        await gs_client.insert_sync_df(pd.DataFrame(df_dict), page_name)
    except Exception as e:
        logger.error(f"Ошибка синхронизации {e}")
        traceback.print_exc()
        return False
    return True
