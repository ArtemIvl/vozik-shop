# update_active_referrals.py
import asyncio
from sqlalchemy import select, func, distinct
from db.session import SessionLocal
from db.models.user import User
from db.models.order import Order, OrderStatus


async def main():
    async with SessionLocal() as session:
        # Step 1: get mapping of referrer_id -> active referral count
        result = await session.execute(
            select(User.referred_by, func.count(distinct(User.id)))
            .join(Order, Order.user_id == User.id)
            .where(User.referred_by.isnot(None))
            .where(Order.status == OrderStatus.PAID)
            .group_by(User.referred_by)
        )

        referral_counts = dict(result.all())
        print("Referral counts found:", referral_counts)

        # Step 2: fetch all users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        updated = 0
        for user in users:
            new_count = referral_counts.get(user.id, 0)
            if user.active_referral_count != new_count:
                user.active_referral_count = new_count
                updated += 1

        await session.commit()
        print(f"Updated {updated} users with active referral counts")


if __name__ == "__main__":
    asyncio.run(main())
