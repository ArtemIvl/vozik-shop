from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.sell_star_order import SellStarOrder, SellStarOrderStatus
from db.models.user import User
from services.profile_stats import SELL_STARS_EXPIRES_SECONDS


async def create_sell_star_order(
    session: AsyncSession,
    user_id: int,
    stars_amount: int,
    payout_usdt: Decimal,
) -> SellStarOrder:
    order = SellStarOrder(
        user_id=user_id,
        stars_amount=stars_amount,
        payout_ton=payout_usdt,
        status=SellStarOrderStatus.PENDING,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_sell_star_order_by_id(
    session: AsyncSession,
    order_id: int,
) -> SellStarOrder | None:
    result = await session.execute(
        select(SellStarOrder).where(SellStarOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def mark_sell_star_order_paid(
    session: AsyncSession,
    order_id: int,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: str | None,
) -> bool:
    result = await session.execute(
        update(SellStarOrder)
        .where(
            SellStarOrder.id == order_id,
            SellStarOrder.status == SellStarOrderStatus.PENDING,
        )
        .values(
            status=SellStarOrderStatus.PAID,
            telegram_payment_charge_id=telegram_payment_charge_id,
            provider_payment_charge_id=provider_payment_charge_id,
            paid_at=datetime.now(timezone.utc),
        )
    )
    return bool(result.rowcount)


async def cancel_sell_star_order(
    session: AsyncSession,
    order_id: int,
    user_id: int,
) -> bool:
    result = await session.execute(
        update(SellStarOrder)
        .where(
            SellStarOrder.id == order_id,
            SellStarOrder.user_id == user_id,
            SellStarOrder.status == SellStarOrderStatus.PENDING,
        )
        .values(status=SellStarOrderStatus.CANCELLED)
    )
    await session.commit()
    return bool(result.rowcount)


async def expire_pending_sell_star_orders(
    session: AsyncSession,
    user_id: int | None = None,
) -> None:
    cutoff = datetime.now(timezone.utc).timestamp() - SELL_STARS_EXPIRES_SECONDS
    cutoff_dt = datetime.fromtimestamp(cutoff, tz=timezone.utc)

    query = (
        update(SellStarOrder)
        .where(
            SellStarOrder.status == SellStarOrderStatus.PENDING,
            SellStarOrder.created_at < cutoff_dt,
        )
        .values(status=SellStarOrderStatus.CANCELLED)
    )
    if user_id is not None:
        query = query.where(SellStarOrder.user_id == user_id)

    await session.execute(query)
    await session.commit()


async def credit_user_balance_from_sell(
    session: AsyncSession,
    user_id: int,
    payout_usdt: Decimal,
) -> User:
    user = await session.get(User, user_id)
    user.balance += payout_usdt
    await session.commit()
    await session.refresh(user)
    return user
