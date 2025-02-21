from aiogram import Router

from bot.handlers.admin.add_admin import add_admin_router
from bot.handlers.admin.remove_admin import remove_admin_router
from bot.handlers.admin.not_filled_users import not_filled_router
from bot.handlers.admin.remove_event import remove_event_router
from bot.handlers.admin.remove_user import remove_user_router
from bot.handlers.admin.sync_data import sync_router
from bot.middlewares.check_admin_access import CheckAdminAccessMiddleware

admin_router = Router()

admin_router.include_routers(
    not_filled_router,
    add_admin_router,
    remove_admin_router,
    remove_event_router,
    remove_user_router,
    sync_router,
)

admin_router.message.middleware(CheckAdminAccessMiddleware())
