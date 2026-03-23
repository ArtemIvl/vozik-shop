from db.models.order import Order, PaymentType, OrderStatus, OrderType
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from decimal import Decimal
from sqlalchemy import select, update, exists, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone

from db.models.sell_star_order import SellStarOrder, SellStarOrderStatus
from db.models.withdrawal import Withdrawal, WithdrawalStatus
from services.payment import get_ton_price_usd

USD_PRICE_PER_STAR = Decimal("0.015")
HELEKET_NET_RATE = Decimal("0.98")
PREMIUM_MARKUP = Decimal("1.05")
TELEGRAM_STARS_WITHDRAW_FEE = Decimal("0.15")
LOCK_PERIOD_DAYS = 21

async def create_order(session: AsyncSession, user_id: int, to_username: str, stars: int | None, premium_months: int | None, price_ton: Decimal | None,
                       price_usdt: Decimal | None, memo: str, payment_type: PaymentType, order_type: OrderType) -> Order:
    order = Order(
        user_id=user_id,
        to_username=to_username,
        stars_amount=stars,
        premium_months=premium_months,
        price_ton=price_ton,
        price_usdt=price_usdt,
        memo=memo,
        status=OrderStatus.PENDING,
        payment_type=payment_type,
        order_type=order_type
    )
    session.add(order)
    await session.commit()
    return order

async def get_pending_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.user))
        .where(Order.status == OrderStatus.PENDING)
    )
    return result.scalars().all()


async def get_failed_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.user))
        .where(Order.status == OrderStatus.FAILED)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def mark_order_paid(session: AsyncSession, order_id: int) -> None:
    await session.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=OrderStatus.PAID)
    )
    await session.commit()


async def mark_order_failed(session: AsyncSession, order_id: int) -> None:
    await session.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=OrderStatus.FAILED)
    )
    await session.commit()


async def mark_order_cancelled(session: AsyncSession, order_id: int) -> None:
    await session.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=OrderStatus.CANCELLED)
    )
    await session.commit()


async def mark_order_processing(session: AsyncSession, order_id: int) -> None:
    await session.execute(
        update(Order)
        .where(Order.id == order_id, Order.status == OrderStatus.PENDING)
        .values(status=OrderStatus.PROCESSING)
    )
    await session.commit()


async def mark_failed_order_processing(session: AsyncSession, order_id: int) -> bool:
    result = await session.execute(
        update(Order)
        .where(Order.id == order_id, Order.status == OrderStatus.FAILED)
        .values(status=OrderStatus.PROCESSING)
    )
    await session.commit()
    return bool(result.rowcount)


async def get_order_by_id(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order).options(selectinload(Order.user)).filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    return order

async def get_bot_statistics(session: AsyncSession) -> dict:
    ton_price_usd = await get_ton_price_usd()

    orders_result = await session.execute(select(Order).where(Order.status == OrderStatus.PAID))
    orders = orders_result.scalars().all()

    sell_orders_result = await session.execute(
        select(SellStarOrder).where(SellStarOrder.status == SellStarOrderStatus.PAID)
    )
    sell_orders = sell_orders_result.scalars().all()

    user_balance_result = await session.execute(select(func.coalesce(func.sum(User.balance), 0)))
    total_user_balances = Decimal(user_balance_result.scalar() or 0)

    pending_withdrawals_result = await session.execute(
        select(func.coalesce(func.sum(Withdrawal.ton_amount), 0)).where(
            Withdrawal.status == WithdrawalStatus.PENDING
        )
    )
    pending_withdrawals_total = Decimal(pending_withdrawals_result.scalar() or 0)

    referral_result = await session.execute(select(func.coalesce(func.sum(User.total_earned), 0)))
    total_referral_paid = Decimal(referral_result.scalar() or 0)

    total_paid_orders = len(orders)
    total_stars_sold = 0
    total_premium_months = 0

    stars_sales_revenue_usd = Decimal("0")
    stars_sales_cost_usd = Decimal("0")
    stars_sales_profit_usd = Decimal("0")

    premium_revenue_usd = Decimal("0")
    premium_cost_usd = Decimal("0")
    premium_profit_usd = Decimal("0")

    for order in orders:
        order_revenue_usd = Decimal("0")
        order_cost_usd = Decimal("0")

        if order.payment_type == PaymentType.USDT and order.price_usdt is not None:
            order_revenue_usd = Decimal(order.price_usdt) * HELEKET_NET_RATE
        elif order.payment_type == PaymentType.TON and order.price_ton is not None:
            order_revenue_usd = Decimal(order.price_ton) * ton_price_usd

        if order.order_type == OrderType.STARS:
            total_stars_sold += order.stars_amount or 0
            order_cost_usd = USD_PRICE_PER_STAR * Decimal(order.stars_amount or 0)
            stars_sales_revenue_usd += order_revenue_usd
            stars_sales_cost_usd += order_cost_usd
            stars_sales_profit_usd += order_revenue_usd - order_cost_usd
        elif order.order_type == OrderType.PREMIUM:
            total_premium_months += order.premium_months or 0
            margin = PREMIUM_MARKUP
            if order.payment_type == PaymentType.USDT and order.price_usdt is not None:
                order_cost_usd = Decimal(order.price_usdt) / margin
            elif order.payment_type == PaymentType.TON and order.price_ton is not None:
                order_cost_usd = (Decimal(order.price_ton) / margin) * ton_price_usd
            premium_revenue_usd += order_revenue_usd
            premium_cost_usd += order_cost_usd
            premium_profit_usd += order_revenue_usd - order_cost_usd

    total_stars_bought_from_users = 0
    total_paid_to_users_usdt = Decimal("0")

    lock_cutoff = datetime.now(timezone.utc) - timedelta(days=LOCK_PERIOD_DAYS)
    locked_stars_total = 0
    unlocked_stars_total = 0

    for sell_order in sell_orders:
        stars_amount = sell_order.stars_amount or 0
        payout_usdt = Decimal(sell_order.payout_ton or 0)
        total_stars_bought_from_users += stars_amount
        total_paid_to_users_usdt += payout_usdt

        locked_reference = sell_order.paid_at or sell_order.created_at
        if locked_reference and locked_reference >= lock_cutoff:
            locked_stars_total += stars_amount
        else:
            unlocked_stars_total += stars_amount

    total_withdrawable_after_fee_stars = Decimal(total_stars_bought_from_users) * (Decimal("1") - TELEGRAM_STARS_WITHDRAW_FEE)
    locked_withdrawable_after_fee_stars = Decimal(locked_stars_total) * (Decimal("1") - TELEGRAM_STARS_WITHDRAW_FEE)
    unlocked_withdrawable_after_fee_stars = Decimal(unlocked_stars_total) * (Decimal("1") - TELEGRAM_STARS_WITHDRAW_FEE)

    gross_inventory_value_usdt = Decimal(total_stars_bought_from_users) * USD_PRICE_PER_STAR
    net_inventory_value_after_fee_usdt = total_withdrawable_after_fee_stars * USD_PRICE_PER_STAR
    locked_inventory_value_after_fee_usdt = locked_withdrawable_after_fee_stars * USD_PRICE_PER_STAR
    unlocked_inventory_value_after_fee_usdt = unlocked_withdrawable_after_fee_stars * USD_PRICE_PER_STAR
    inventory_expected_profit_usdt = net_inventory_value_after_fee_usdt - total_paid_to_users_usdt

    realized_profit_before_referrals_usdt = stars_sales_profit_usd + premium_profit_usd
    realized_profit_after_referrals_usdt = realized_profit_before_referrals_usdt - total_referral_paid
    total_user_liabilities_usdt = total_user_balances + pending_withdrawals_total

    return {
        "ton_price_usd": ton_price_usd.quantize(Decimal("0.01")),
        "total_paid_orders": total_paid_orders,
        "total_stars_sold": total_stars_sold,
        "total_premium_months": total_premium_months,
        "stars_sales_revenue_usd": stars_sales_revenue_usd.quantize(Decimal("0.01")),
        "stars_sales_cost_usd": stars_sales_cost_usd.quantize(Decimal("0.01")),
        "stars_sales_profit_usd": stars_sales_profit_usd.quantize(Decimal("0.01")),
        "premium_revenue_usd": premium_revenue_usd.quantize(Decimal("0.01")),
        "premium_cost_usd": premium_cost_usd.quantize(Decimal("0.01")),
        "premium_profit_usd": premium_profit_usd.quantize(Decimal("0.01")),
        "total_stars_bought_from_users": total_stars_bought_from_users,
        "total_paid_to_users_usdt": total_paid_to_users_usdt.quantize(Decimal("0.01")),
        "locked_stars_total": locked_stars_total,
        "unlocked_stars_total": unlocked_stars_total,
        "total_withdrawable_after_fee_stars": total_withdrawable_after_fee_stars.quantize(Decimal("0.01")),
        "locked_withdrawable_after_fee_stars": locked_withdrawable_after_fee_stars.quantize(Decimal("0.01")),
        "unlocked_withdrawable_after_fee_stars": unlocked_withdrawable_after_fee_stars.quantize(Decimal("0.01")),
        "gross_inventory_value_usdt": gross_inventory_value_usdt.quantize(Decimal("0.01")),
        "net_inventory_value_after_fee_usdt": net_inventory_value_after_fee_usdt.quantize(Decimal("0.01")),
        "locked_inventory_value_after_fee_usdt": locked_inventory_value_after_fee_usdt.quantize(Decimal("0.01")),
        "unlocked_inventory_value_after_fee_usdt": unlocked_inventory_value_after_fee_usdt.quantize(Decimal("0.01")),
        "inventory_expected_profit_usdt": inventory_expected_profit_usdt.quantize(Decimal("0.01")),
        "total_referral_paid": total_referral_paid.quantize(Decimal("0.01")),
        "total_user_balances": total_user_balances.quantize(Decimal("0.01")),
        "pending_withdrawals_total": pending_withdrawals_total.quantize(Decimal("0.01")),
        "total_user_liabilities_usdt": total_user_liabilities_usdt.quantize(Decimal("0.01")),
        "realized_profit_before_referrals_usdt": realized_profit_before_referrals_usdt.quantize(Decimal("0.01")),
        "realized_profit_after_referrals_usdt": realized_profit_after_referrals_usdt.quantize(Decimal("0.01")),
    }


async def has_user_paid_orders(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(exists().where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PAID
        ))
    )
    return result.scalar()
