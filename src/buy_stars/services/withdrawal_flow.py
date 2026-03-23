from datetime import datetime
from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order import Order, OrderStatus
from db.models.sell_star_order import SellStarOrder, SellStarOrderStatus
from db.models.user import User
from db.models.withdrawal import Withdrawal, WithdrawalStatus
from keyboards.admin_keyboards import withdraw_info_keyboard
from requests.user_requests import get_all_admins, get_user_by_id


def _fmt_decimal(value: Decimal | int | None, places: int = 4) -> str:
    if value is None:
        value = Decimal("0")
    quant = Decimal("1").scaleb(-places)
    return f"{Decimal(value).quantize(quant):f}"


async def get_withdrawal_snapshot(
    session: AsyncSession,
    user: User,
    withdrawal: Withdrawal,
) -> dict:
    sell_stats = await session.execute(
        select(
            func.count(SellStarOrder.id),
            func.coalesce(func.sum(SellStarOrder.stars_amount), 0),
            func.coalesce(func.sum(SellStarOrder.payout_ton), 0),
        ).where(
            SellStarOrder.user_id == user.id,
            SellStarOrder.status == SellStarOrderStatus.PAID,
        )
    )
    sell_orders_count, sold_stars_total, sold_payout_total = sell_stats.one()

    buy_stats = await session.execute(
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.stars_amount), 0),
            func.coalesce(func.sum(Order.premium_months), 0),
        ).where(
            Order.user_id == user.id,
            Order.status == OrderStatus.PAID,
        )
    )
    paid_orders_count, bought_stars_total, bought_premium_months = buy_stats.one()

    approved_withdraw_stats = await session.execute(
        select(
            func.count(Withdrawal.id),
            func.coalesce(func.sum(Withdrawal.ton_amount), 0),
        ).where(
            Withdrawal.user_id == user.id,
            Withdrawal.status == WithdrawalStatus.APPROVED,
        )
    )
    approved_withdrawals_count, approved_withdrawals_total = approved_withdraw_stats.one()

    referrer = await get_user_by_id(session, user.referred_by) if user.referred_by else None
    balance_after_request = Decimal(user.balance or 0)
    request_amount = Decimal(withdrawal.ton_amount or 0)

    return {
        "referrer_username": referrer.username if referrer and referrer.username else None,
        "paid_orders_count": paid_orders_count or 0,
        "bought_stars_total": bought_stars_total or 0,
        "bought_premium_months": bought_premium_months or 0,
        "sell_orders_count": sell_orders_count or 0,
        "sold_stars_total": sold_stars_total or 0,
        "sold_payout_total": Decimal(sold_payout_total or 0),
        "approved_withdrawals_count": approved_withdrawals_count or 0,
        "approved_withdrawals_total": Decimal(approved_withdrawals_total or 0),
        "balance_after_request": balance_after_request,
        "balance_before_request": balance_after_request + request_amount,
    }


async def build_withdrawal_admin_message(
    session: AsyncSession,
    user: User,
    withdrawal: Withdrawal,
) -> str:
    snapshot = await get_withdrawal_snapshot(session, user, withdrawal)
    username = f"@{user.username}" if user.username else "без username"
    referrer = f"@{snapshot['referrer_username']}" if snapshot["referrer_username"] else "нет"
    registered_at = (
        user.reg_date.strftime("%d.%m.%Y %H:%M")
        if isinstance(user.reg_date, datetime)
        else str(user.reg_date)
    )

    return (
        f"🌐 Новая заявка на вывод #{withdrawal.id}\n\n"
        f"👤 Пользователь: {username} | <code>{user.telegram_id}</code>\n"
        f"💳 Кошелёк: <code>{withdrawal.ton_address}</code>\n"
        f"💸 Запрошено: {_fmt_decimal(withdrawal.ton_amount)} USDT\n"
        f"🏦 Баланс до заявки: {_fmt_decimal(snapshot['balance_before_request'])} USDT\n"
        f"🏦 Баланс после заявки: {_fmt_decimal(snapshot['balance_after_request'])} USDT\n\n"
        f"🤝 Рефералка\n"
        f"Реферер: {referrer}\n"
        f"Рефералов: {user.referral_count or 0}\n"
        f"Активных рефералов: {user.active_referral_count or 0}\n"
        f"Всего заработано: {_fmt_decimal(user.total_earned)} USDT\n"
        f"Комиссия: {_fmt_decimal(Decimal(user.referral_commission or 0) * Decimal('100'), 2)}%\n\n"
        f"⭐ Sell Stars статистика\n"
        f"Оплаченных sell orders: {snapshot['sell_orders_count']}\n"
        f"Продано звёзд: {snapshot['sold_stars_total']}\n"
        f"Начислено за sell stars: {_fmt_decimal(snapshot['sold_payout_total'])} USDT\n\n"
        f"🛍 Покупки в боте\n"
        f"Оплаченных заказов: {snapshot['paid_orders_count']}\n"
        f"Куплено звёзд: {snapshot['bought_stars_total']}\n"
        f"Месяцев premium: {snapshot['bought_premium_months']}\n\n"
        f"📤 История выводов\n"
        f"Одобрено выводов: {snapshot['approved_withdrawals_count']}\n"
        f"Выведено ранее: {_fmt_decimal(snapshot['approved_withdrawals_total'])} USDT\n\n"
        f"🕒 Дата регистрации: {registered_at}"
    )


async def notify_admins_about_withdrawal(
    bot: Bot,
    session: AsyncSession,
    user: User,
    withdrawal: Withdrawal,
) -> None:
    admins = await get_all_admins(session)
    message = await build_withdrawal_admin_message(session, user, withdrawal)

    for admin in admins:
        try:
            await bot.send_message(
                admin.telegram_id,
                message,
                parse_mode="HTML",
                reply_markup=withdraw_info_keyboard(withdrawal.id),
            )
        except TelegramForbiddenError:
            continue
