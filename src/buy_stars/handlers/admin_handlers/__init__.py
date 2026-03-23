from aiogram import Router
from filters.is_admin import IsAdmin

from .base_admin import base_admin_router
from .user_admin import user_admin_router
from .withdrawal_admin import withdraw_admin_router
from .stats_admin import stats_admin_router
from .send_message_admin import message_admin_router
from .failed_orders_admin import failed_orders_admin_router


def register_admin_handlers(dp):
    admin_router = Router()
    admin_router.message.filter(IsAdmin())
    admin_router.callback_query.filter(IsAdmin())

    admin_router.include_router(base_admin_router)
    admin_router.include_router(user_admin_router)
    admin_router.include_router(withdraw_admin_router)
    admin_router.include_router(failed_orders_admin_router)
    admin_router.include_router(stats_admin_router)
    admin_router.include_router(message_admin_router)

    dp.include_router(admin_router)
