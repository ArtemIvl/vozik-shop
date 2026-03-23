import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.start_handlers import register_start_handlers
from handlers.buy_stars_handlers import register_buy_stars_handlers
from handlers.profile_handlers import register_profile_handlers
from services.payment_checker import check_payments
from handlers.admin_handlers import register_admin_handlers
from handlers.withdrawal_handlers import register_withdrawal_handlers
from handlers.buy_tg_premium_handlers import register_buy_tg_premium_handlers
from handlers.language_handlers import register_language_handlers
from handlers.gift_promo_handlers import register_gift_promo_handlers
from handlers.sell_stars_handlers import register_sell_stars_handlers
from db.session import init_models
from middlewares.private_chat_only import PrivateChatOnlyMiddleware
from middlewares.username_tracking import UserTrackingMiddleware
from middlewares.ban_check import BanCheckMiddleware

# Настройка логов
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Middleware
dp.message.middleware(PrivateChatOnlyMiddleware())
dp.callback_query.middleware(PrivateChatOnlyMiddleware())
dp.message.middleware(UserTrackingMiddleware())
dp.callback_query.middleware(UserTrackingMiddleware())
dp.message.middleware(BanCheckMiddleware())
dp.callback_query.middleware(BanCheckMiddleware())

register_start_handlers(dp)
register_buy_stars_handlers(dp)
register_profile_handlers(dp)
register_admin_handlers(dp)
register_withdrawal_handlers(dp)
register_buy_tg_premium_handlers(dp)
register_language_handlers(dp)
register_gift_promo_handlers(dp)
register_sell_stars_handlers(dp)


async def payment_checker_loop():
    while True:
        try:
            await check_payments(bot)
        except Exception as e:
            print(f"[payment_checker_loop] Error: {e}")
        await asyncio.sleep(30)  # каждые 30 секунд


async def main():
    await init_models()
    asyncio.create_task(payment_checker_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
