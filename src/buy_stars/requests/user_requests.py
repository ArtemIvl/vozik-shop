from db.models.user import User, Language
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from db.models.order import OrderType, Order, OrderStatus
from datetime import datetime, timezone
from services.payment import get_ton_price_usd

async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    user = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    if user:
        return user.scalars().first()
    
 
async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    user = await session.execute(select(User).filter(User.id == user_id))
    if user:
        return user.scalars().first()


async def add_user(
    session: AsyncSession, telegram_id: int, username: str, referred_by: int, language: Language
) -> None:
    user = User(
        telegram_id=telegram_id,
        username=username,
        referred_by=referred_by,
        language=language
    )
    session.add(user)
    await session.commit()


async def ban_user(session: AsyncSession, user: User) -> None:
    user.is_banned = True
    await session.commit()


async def unban_user(session: AsyncSession, user: User) -> None:
    user.is_banned = False
    await session.commit()


async def change_referral_commission(session: AsyncSession, user: User, new_commission: Decimal) -> None:
    user.referral_commission = new_commission
    await session.commit()


async def check_admin(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        return user.is_admin
    else:
        return False


async def add_admin(session: AsyncSession, user: User) -> None:
    user.is_admin = True
    await session.commit()


async def remove_admin(session: AsyncSession, user: User) -> None:
    user.is_admin = False
    await session.commit()


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def get_total_users(session: AsyncSession):
    query = select(func.count(User.id))
    result = await session.execute(query)
    total_users = result.scalar()
    return total_users

async def update_user_username(
    session: AsyncSession, user: User, new_username: str
) -> None:
    if user.username != new_username:
        user.username = new_username
        await session.commit()


async def increment_referral_count(session: AsyncSession, referrer_id: int):
    referrer = await session.get(User, referrer_id)
    if referrer:
        referrer.referral_count += 1
        await session.commit()


async def check_and_increment_active_referral(session: AsyncSession, buyer_id: int) -> bool:
    buyer = await session.get(User, buyer_id)
    if not buyer or not buyer.referred_by:
        return False
    
    paid_orders_count = await session.scalar(
        select(func.count(Order.id)).where(
            Order.user_id == buyer.id,
            Order.status == OrderStatus.PAID
        )
    )

    if paid_orders_count != 1:
        return False
    
    referrer = await session.get(User, buyer.referred_by)
    if referrer:
        referrer.active_referral_count += 1
        await session.commit()
        return True

    return False


async def get_all_admins(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).filter(User.is_admin == True))
    return result.scalars().all()

async def add_referral_bonus_usd(session: AsyncSession, user: User, price_usd: Decimal, order_type: OrderType) -> list[tuple[User, Decimal]]:
    bonuses: list[tuple[User, Decimal]] = []
    if not user.referred_by:
        return bonuses
    
    referrer = await session.get(User, user.referred_by)
    if not referrer:
        return bonuses
    
    received = price_usd * Decimal("0.98")
    margin = Decimal("1.05") if order_type == OrderType.PREMIUM else Decimal("1.14")
    cost = price_usd / margin
    profit = received - cost
    if profit <= 0:
        return bonuses
    
    # Прямой бонус
    bonus_1 = profit * (referrer.referral_commission or Decimal("0.1"))
    referrer.balance += bonus_1
    referrer.total_earned += bonus_1
    bonuses.append((referrer, bonus_1))

    # Бонус второго уровня
    if referrer.referred_by:
        referrer2 = await session.get(User, referrer.referred_by)
        if referrer2:
            bonus_2 = profit * Decimal("0.05")
            referrer2.balance += bonus_2
            referrer2.total_earned += bonus_2
            bonuses.append((referrer2, bonus_2))

    await session.commit()
    return bonuses

async def add_referral_bonus(session: AsyncSession, user: User, price_ton: Decimal, order_type: OrderType) -> list[tuple[User, Decimal]]:
    bonuses: list[tuple[User, Decimal]] = []

    if not user.referred_by:
        return bonuses

    referrer = await session.get(User, user.referred_by)
    if not referrer:
        return bonuses

    margin = Decimal("1.05") if order_type == OrderType.PREMIUM else Decimal("1.11")
    cost = price_ton / margin
    profit_ton = price_ton - cost
    if profit_ton <= 0:
        return bonuses

    ton_price_usd = await get_ton_price_usd()
    profit = (profit_ton * ton_price_usd).quantize(Decimal("0.0001"))
    if profit <= 0:
        return bonuses
    
    # Прямой бонус
    bonus_1 = profit * (referrer.referral_commission or Decimal("0.1"))
    referrer.balance += bonus_1
    referrer.total_earned += bonus_1
    bonuses.append((referrer, bonus_1))

    # Бонус второго уровня
    if referrer.referred_by:
        referrer2 = await session.get(User, referrer.referred_by)
        if referrer2:
            bonus_2 = profit * Decimal("0.05")
            referrer2.balance += bonus_2
            referrer2.total_earned += bonus_2
            bonuses.append((referrer2, bonus_2))

    await session.commit()
    return bonuses

async def set_user_language(session: AsyncSession, telegram_id: int, language: Language) -> None:
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        user.language = language
        await session.commit()


async def set_user_default_ton_wallet(session: AsyncSession, user: User | None, wallet: str | None) -> None:
    if not user:
        return
    normalized_wallet = wallet.strip() if wallet else None
    normalized_wallet = normalized_wallet or None
    if user.default_ton_wallet != normalized_wallet:
        user.default_ton_wallet = normalized_wallet
        await session.commit()
