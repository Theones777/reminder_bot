import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# from bot.handlers.admin.init_handler import admin_router
from bot.handlers.user import user_router
from bot.handlers.common import common_router
from bot.utils import set_commands, remind
from config import Config


async def main():
    # bot init
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(
        token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # include routers
    dp.include_router(common_router)
    # dp.include_router(admin_router)
    dp.include_router(user_router)

    # set menu buttons
    await set_commands(bot)

    # make periodic mailing
    asyncio.create_task(remind(bot))

    # bot start
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
