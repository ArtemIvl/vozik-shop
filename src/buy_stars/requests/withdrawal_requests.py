from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from db.models.withdrawal import Withdrawal, WithdrawalStatus
from requests.user_requests import get_user_by_id


async def create_withdrawal_request(
    session: AsyncSession, user_id: int, amount: Decimal, address: str
) -> Withdrawal:

    user = await get_user_by_id(session, user_id)
    if user.referral_balance < amount:
        raise ValueError("Insufficient stars for withdrawal.")
    user.referral_balance -= amount

    withdrawal = Withdrawal(
        user_id=user_id,
        ton_amount=amount,
        ton_address=address,
        status=WithdrawalStatus.PENDING,
    )
    session.add_all([user, withdrawal])

    await session.commit()
    return withdrawal


async def get_pending_withdrawals(session: AsyncSession) -> list[Withdrawal]:
    result = await session.execute(
        select(Withdrawal).where(Withdrawal.status == WithdrawalStatus.PENDING)
    )
    return result.scalars().all()


async def approve_withdrawal(session: AsyncSession, withdrawal_id: int) -> None:
    await session.execute(
        update(Withdrawal)
        .where(Withdrawal.id == withdrawal_id)
        .values(status=WithdrawalStatus.APPROVED)
    )
    await session.commit()


async def reject_withdrawal(session: AsyncSession, withdrawal_id: int) -> None:
    withdrawal = await session.get(Withdrawal, withdrawal_id)
    if withdrawal:
        withdrawal.status = WithdrawalStatus.REJECTED
        await session.commit()
    else:
        raise ValueError(f"Withdrawal with id {withdrawal_id} not found.")


async def reject_withdrawal_and_refund(session: AsyncSession, withdrawal_id: int) -> None:
    withdrawal = await session.get(Withdrawal, withdrawal_id)
    if not withdrawal:
        raise ValueError(f"Withdrawal with id {withdrawal_id} not found.")
    if withdrawal.status != WithdrawalStatus.PENDING:
        return

    user = await get_user_by_id(session, withdrawal.user_id)
    user.referral_balance += Decimal(withdrawal.ton_amount)
    withdrawal.status = WithdrawalStatus.REJECTED
    await session.commit()


async def get_withdrawal_by_id(session: AsyncSession, withdrawal_id: int) -> Withdrawal | None:
    withdrawal = await session.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    if withdrawal:
        return withdrawal.scalars().first()
    else:
        return None
