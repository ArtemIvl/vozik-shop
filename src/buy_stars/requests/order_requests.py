from db.models.order import Order, PaymentType, OrderStatus, OrderType
from sqlalchemy.ext.asyncio import AsyncSession
from db.models.user import User
from decimal import Decimal
from sqlalchemy import select, update, exists
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

USD_PRICE_PER_STAR = 0.015

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
    result = await session.execute(
        select(Order).where(Order.status == OrderStatus.PAID)
    )
    orders = result.scalars().all()

    total_stars = 0
    total_premium = 0
    total_ton_spent = Decimal("0")
    total_usdt_spent = Decimal("0")
    ton_profit = Decimal("0")
    usdt_profit = Decimal("0")

    for order in orders:
        if order.stars_amount:
            total_stars += order.stars_amount
        if order.premium_months:
            total_premium += order.premium_months

        if order.payment_type == PaymentType.TON:
            total_ton_spent += order.price_ton
            margin = Decimal("1.05") if order.order_type == OrderType.PREMIUM else Decimal("1.11")
            cost = order.price_ton / margin
            ton_profit += order.price_ton - cost

        if order.payment_type == PaymentType.USDT:
            total_usdt_spent += order.price_usdt
            received = order.price_usdt * Decimal("0.98")
            margin = Decimal("1.05") if order.order_type == OrderType.PREMIUM else Decimal("1.14")
            cost = order.price_usdt / margin
            usdt_profit += received - cost

    referral_result = await session.execute(select(User.referral_total_earned))
    total_referral_paid = sum(referral_result.scalars().all() or [])

    return {
        "total_stars": total_stars,
        "total_premium": total_premium,
        "total_ton_spent": round(total_ton_spent, 2),
        "total_usdt_spent": round(total_usdt_spent, 2),
        "ton_profit": round(ton_profit - total_referral_paid, 2),
        "usdt_profit": round(usdt_profit, 2),
    }


async def has_user_paid_orders(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(exists().where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PAID
        ))
    )
    return result.scalar()
