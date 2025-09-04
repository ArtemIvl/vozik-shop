from fastapi import APIRouter, Query, Depends
from requests.user_requests import get_user_by_telegram_id
from requests.order_requests import has_user_paid_orders
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_session

router = APIRouter(prefix="/external", tags=["external"])

@router.get("/is_registered")
async def is_registered(
    telegram_id: int = Query(...),
    referrer_telegram_id: int = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    user = await get_user_by_telegram_id(session, telegram_id)
    is_member = bool(user)

    is_referrer = False
    if user:
        referrer = await get_user_by_telegram_id(session, referrer_telegram_id)
        if referrer and user.referred_by == referrer.id:
            is_referrer = True
    
    # isCompleted — оба условия выполнены
    is_completed = is_member and is_referrer

    return {
        "isMember": is_member,
        "isReferrer": is_referrer,
        "isCompleted": is_completed
    }


@router.get("/is_registered_and_paid")
async def is_registered_and_paid(
    telegram_id: int = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    # Проверка — зарегистрирован ли пользователь
    user = await get_user_by_telegram_id(session, telegram_id)
    is_member = bool(user)

    # Проверка — оплачивал ли заказы
    paid = False
    if is_member:
        paid = await has_user_paid_orders(session, user.id)

    # isCompleted — все 3 условия выполнены
    is_completed = is_member and paid

    return {
        "isMember": is_member,
        "isPaid": paid,
        "isCompleted": is_completed
    }