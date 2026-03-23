from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order import Order, OrderStatus
from db.models.sell_star_order import SellStarOrder, SellStarOrderStatus
from db.models.user import User

SELL_STARS_EXPIRES_SECONDS = 1800


def format_decimal(value: Decimal | int | None, places: int = 4) -> str:
    if value is None:
        value = Decimal("0")
    quant = Decimal("1").scaleb(-places)
    return f"{Decimal(value).quantize(quant):f}"


def get_remaining_seconds(created_at, ttl_seconds: int = SELL_STARS_EXPIRES_SECONDS) -> int:
    if not created_at:
        return ttl_seconds
    elapsed = int((datetime.now(timezone.utc) - created_at).total_seconds())
    return max(0, ttl_seconds - elapsed)


def is_expired(created_at, ttl_seconds: int = SELL_STARS_EXPIRES_SECONDS) -> bool:
    return get_remaining_seconds(created_at, ttl_seconds) <= 0


async def get_profile_stats(session: AsyncSession, user: User) -> dict:
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
    total_orders_count, purchased_stars_total, premium_months_total = buy_stats.one()

    sell_stats = await session.execute(
        select(
            func.coalesce(func.sum(SellStarOrder.stars_amount), 0),
            func.coalesce(func.sum(SellStarOrder.payout_ton), 0),
        ).where(
            SellStarOrder.user_id == user.id,
            SellStarOrder.status == SellStarOrderStatus.PAID,
        )
    )
    exchanged_stars_total, received_ton_total = sell_stats.one()

    paid_buy_rows = await session.execute(
        select(
            User.id,
            func.coalesce(func.sum(Order.stars_amount), 0),
            func.coalesce(func.sum(Order.premium_months), 0),
        )
        .outerjoin(
            Order,
            (Order.user_id == User.id) & (Order.status == OrderStatus.PAID),
        )
        .group_by(User.id)
    )
    sell_rows = await session.execute(
        select(
            User.id,
            func.coalesce(func.sum(SellStarOrder.stars_amount), 0),
        )
        .outerjoin(
            SellStarOrder,
            (SellStarOrder.user_id == User.id) & (SellStarOrder.status == SellStarOrderStatus.PAID),
        )
        .group_by(User.id)
    )
    referral_rows = await session.execute(select(User.id, User.active_referral_count))

    scores: dict[int, int] = {}
    for user_id, stars_bought, premium_months in paid_buy_rows:
        scores[user_id] = int(stars_bought or 0) + int(premium_months or 0) * 100
    for user_id, stars_sold in sell_rows:
        scores[user_id] = scores.get(user_id, 0) + int(stars_sold or 0)
    for user_id, active_referrals in referral_rows:
        scores[user_id] = scores.get(user_id, 0) + int(active_referrals or 0) * 100

    current_score = scores.get(user.id, 0)
    other_scores = [score for user_id, score in scores.items() if user_id != user.id]
    if not other_scores:
        outperform_percent = 100
    else:
        outperform_percent = round((sum(1 for score in other_scores if current_score > score) / len(other_scores)) * 100)

    received_ton_decimal = Decimal(received_ton_total or 0)
    referral_earned_decimal = Decimal(user.referral_total_earned or 0)

    return {
        "totalOrdersCount": total_orders_count or 0,
        "purchasedStarsTotal": purchased_stars_total or 0,
        "premiumMonthsTotal": premium_months_total or 0,
        "exchangedStarsTotal": exchanged_stars_total or 0,
        "receivedTonTotal": format_decimal(received_ton_decimal, places=4),
        "referralEarnedTon": format_decimal(referral_earned_decimal, places=4),
        "totalEarnedTon": format_decimal(received_ton_decimal + referral_earned_decimal, places=4),
        "scorePoints": current_score,
        "outperformPercent": outperform_percent,
    }
