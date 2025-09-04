from aiogram import F, Router, types
from requests.order_requests import get_bot_statistics
from keyboards.admin_keyboards import admin_back_keyboard
from db.session import SessionLocal

stats_admin_router = Router()

@stats_admin_router.callback_query(F.data == "bot_stats")
async def bot_stats_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        stats = await get_bot_statistics(session)

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"⭐️ Total stars bought: <b>{stats['total_stars']}</b>\n"
        f"💎 Total premium months: <b>{stats['total_premium']}</b>\n\n"
        f"🪙 Total TON spent: <b>{stats['total_ton_spent']:.2f} TON</b>\n"
        f"💰 Profit in TON: <b>{stats['ton_profit']:.2f} TON</b>\n\n"
        f"💵 Total USDT spent: <b>{stats['total_usdt_spent']:.2f} USDT</b>\n"
        f"💰 Profit in USDT: <b>{stats['usdt_profit']:.2f} USDT</b>\n"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())