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
        "📊 <b>Bot Finance Overview</b>\n"
        f"<blockquote>TON/USD now: <b>{stats['ton_price_usd']}</b>\n"
        f"Paid orders: <b>{stats['total_paid_orders']}</b></blockquote>\n\n"
        f"💸 <b>Sales to users</b>\n"
        f"<blockquote>Stars sold: <b>{stats['total_stars_sold']}</b>\n"
        f"Premium months sold: <b>{stats['total_premium_months']}</b>\n"
        f"Stars revenue: <b>{stats['stars_sales_revenue_usd']} USDT</b>\n"
        f"Stars cost: <b>{stats['stars_sales_cost_usd']} USDT</b>\n"
        f"Stars profit: <b>{stats['stars_sales_profit_usd']} USDT</b>\n"
        f"Premium revenue: <b>{stats['premium_revenue_usd']} USDT</b>\n"
        f"Premium cost: <b>{stats['premium_cost_usd']} USDT</b>\n"
        f"Premium profit: <b>{stats['premium_profit_usd']} USDT</b></blockquote>\n\n"
        f"📥 <b>Stars bought from users</b>\n"
        f"<blockquote>Bought stars: <b>{stats['total_stars_bought_from_users']}</b>\n"
        f"Paid to users: <b>{stats['total_paid_to_users_usdt']} USDT</b>\n"
        f"Gross star value: <b>{stats['gross_inventory_value_usdt']} USDT</b>\n"
        f"Net value after Telegram 15% fee: <b>{stats['net_inventory_value_after_fee_usdt']} USDT</b>\n"
        f"Expected profit on bought stars: <b>{stats['inventory_expected_profit_usdt']} USDT</b></blockquote>\n\n"
        f"🔒 <b>Locked inventory (21 days)</b>\n"
        f"<blockquote>Locked stars: <b>{stats['locked_stars_total']}</b>\n"
        f"Locked usable after 15% fee: <b>{stats['locked_withdrawable_after_fee_stars']}</b>\n"
        f"Locked value after fee: <b>{stats['locked_inventory_value_after_fee_usdt']} USDT</b>\n"
        f"Available stars: <b>{stats['unlocked_stars_total']}</b>\n"
        f"Available usable after 15% fee: <b>{stats['unlocked_withdrawable_after_fee_stars']}</b>\n"
        f"Available value after fee: <b>{stats['unlocked_inventory_value_after_fee_usdt']} USDT</b></blockquote>\n\n"
        f"🏦 <b>Liabilities</b>\n"
        f"<blockquote>User balances: <b>{stats['total_user_balances']} USDT</b>\n"
        f"Pending withdrawals: <b>{stats['pending_withdrawals_total']} USDT</b>\n"
        f"Total owed to users: <b>{stats['total_user_liabilities_usdt']} USDT</b>\n"
        f"Referral commissions paid: <b>{stats['total_referral_paid']} USDT</b></blockquote>\n\n"
        f"📈 <b>Profit summary</b>\n"
        f"<blockquote>Realized profit before referrals: <b>{stats['realized_profit_before_referrals_usdt']} USDT</b>\n"
        f"Realized profit after referrals: <b>{stats['realized_profit_after_referrals_usdt']} USDT</b>\n"
        f"Potential inventory profit: <b>{stats['inventory_expected_profit_usdt']} USDT</b></blockquote>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back_keyboard())
