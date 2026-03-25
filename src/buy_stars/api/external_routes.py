from decimal import Decimal, ROUND_UP
from datetime import datetime, timezone
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from requests.user_requests import get_user_by_telegram_id, set_user_default_ton_wallet
from requests.order_requests import has_user_paid_orders, create_order
from requests.user_requests import set_user_language
from requests.sell_star_order_requests import (
    create_sell_star_order,
    get_sell_star_order_by_id,
    cancel_sell_star_order,
    delete_sell_star_order,
    expire_pending_sell_star_orders,
)
from requests.withdrawal_requests import create_withdrawal_request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_async_session
from db.models.order import PaymentType, OrderType, OrderStatus, Order
from db.models.sell_star_order import SellStarOrder, SellStarOrderStatus
from db.models.user import Language
from services.payment import (
    generate_memo,
    calculate_star_price_in_ton,
    calculate_premium_price_in_ton,
    calculate_sell_stars_payout_in_usdt,
)
from services.heleket import create_heleket_invoice
from config import BOT_TOKEN, TON_WALLET_ADDRESS
from services.localization import get_lang, t
from services.profile_stats import (
    format_decimal,
    get_profile_stats,
    get_remaining_seconds,
    is_expired,
)
from services.ton_wallets import normalize_ton_wallet
from services.withdrawal_flow import notify_admins_about_withdrawal
from aiogram import Bot
from aiogram.types import LabeledPrice
from aiogram.exceptions import TelegramForbiddenError

router = APIRouter(prefix="/external", tags=["external"])
PREMIUM_PRICES_USD = {
    3: Decimal("12"),
    6: Decimal("16"),
    12: Decimal("29"),
}
SUPPORT_URL = "https://t.me/VozikShop_support"
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None


class MiniAppStarsOrderPayload(BaseModel):
    init_data: str
    for_self: bool = True
    to_username: str | None = None
    stars_amount: int = Field(..., ge=50)
    payment_method: Literal["TON", "USDT"]


class MiniAppPremiumOrderPayload(BaseModel):
    init_data: str
    for_self: bool = True
    to_username: str | None = None
    months: Literal[3, 6, 12]
    payment_method: Literal["TON", "USDT"]


class MiniAppPendingOrdersPayload(BaseModel):
    init_data: str
    order_type: Literal["stars", "premium"] | None = None


class MiniAppPaymentConfirmPayload(BaseModel):
    init_data: str
    order_id: int
    order_type: Literal["stars", "premium"] | None = None


class MiniAppAuthPayload(BaseModel):
    init_data: str


class MiniAppWithdrawPayload(BaseModel):
    init_data: str
    amount: Decimal
    wallet: str | None = None


class MiniAppWalletSetPayload(BaseModel):
    init_data: str
    wallet: str


class MiniAppLanguageSetPayload(BaseModel):
    init_data: str
    language: Literal["en", "ru", "ua"]


class MiniAppOrderCancelPayload(BaseModel):
    init_data: str
    order_id: int


class MiniAppOrderPaymentLinkPayload(BaseModel):
    init_data: str
    order_id: int


class MiniAppSellStarsOrderPayload(BaseModel):
    init_data: str
    stars_amount: int = Field(..., ge=50)


class MiniAppSellStarsQuotePayload(BaseModel):
    init_data: str
    stars_amount: int = Field(..., ge=50)


class MiniAppStarsQuotePayload(BaseModel):
    init_data: str
    stars_amount: int = Field(..., ge=50)
    payment_method: Literal["TON", "USDT"]


class MiniAppSellStarsInvoicePayload(BaseModel):
    init_data: str
    order_id: int


class MiniAppSellStarsCancelPayload(BaseModel):
    init_data: str
    order_id: int


def verify_telegram_init_data(init_data: str) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Invalid init data hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401, detail="Telegram init data verification failed"
        )

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Missing Telegram user")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid Telegram user payload")

    return user


async def get_authenticated_db_user(session: AsyncSession, init_data: str):
    tg_user = verify_telegram_init_data(init_data)
    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Telegram user id not found")

    user = await get_user_by_telegram_id(session, int(telegram_id))
    if not user:
        raise HTTPException(status_code=404, detail="User is not registered in bot")

    return user, tg_user


def build_tonkeeper_links(price_ton: Decimal, memo: str) -> dict:
    ton_amount = int(price_ton * Decimal("1e9"))
    deep_link = f"ton://transfer/{TON_WALLET_ADDRESS}?amount={ton_amount}&text={memo}"
    web_link = f"https://app.tonkeeper.com/transfer/{TON_WALLET_ADDRESS}?amount={ton_amount}&text={memo}"
    return {
        "tonkeeperUrl": deep_link,
        "tonkeeperWebUrl": web_link,
    }


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
        "isCompleted": is_completed,
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

    return {"isMember": is_member, "isPaid": paid, "isCompleted": is_completed}


@router.post("/miniapp/stars/order")
async def miniapp_create_stars_order(
    payload: MiniAppStarsOrderPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, tg_user = await get_authenticated_db_user(session, payload.init_data)

    if payload.for_self:
        to_username = tg_user.get("username")
    else:
        to_username = (payload.to_username or "").strip().lstrip("@")

    if not to_username:
        raise HTTPException(status_code=400, detail="Target username is required")

    memo = generate_memo()
    payment_type = (
        PaymentType.TON if payload.payment_method == "TON" else PaymentType.USDT
    )

    if payment_type == PaymentType.TON:
        try:
            price = await calculate_star_price_in_ton(payload.stars_amount)
        except Exception as e:
            print(f"[miniapp_create_stars_order] TON price fallback used: {e}")
            price = (
                Decimal(payload.stars_amount) * Decimal("0.015") * Decimal("1.14")
            ).quantize(Decimal("0.001"), rounding=ROUND_UP)
    else:
        price = (
            Decimal(payload.stars_amount) * Decimal("0.015") * Decimal("1.14")
        ).quantize(Decimal("0.01"), rounding=ROUND_UP)

    try:
        order = await create_order(
            session=session,
            user_id=user.id,
            to_username=to_username,
            stars=payload.stars_amount,
            premium_months=None,
            price_ton=price if payment_type == PaymentType.TON else None,
            price_usdt=price if payment_type == PaymentType.USDT else None,
            memo=memo,
            payment_type=payment_type,
            order_type=OrderType.STARS,
        )
    except Exception as e:
        print(f"[miniapp_create_stars_order] create_order failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save order")

    if payment_type == PaymentType.TON:
        tonkeeper_links = build_tonkeeper_links(price, memo)
        return {
            "orderId": order.id,
            "paymentType": "TON",
            "status": order.status.value,
            "starsAmount": payload.stars_amount,
            "toUsername": to_username,
            "priceTon": str(price),
            "walletAddress": TON_WALLET_ADDRESS,
            "memo": memo,
            **tonkeeper_links,
            "expiresInSeconds": 1800,
        }

    try:
        invoice_url = await create_heleket_invoice(amount_usd=price, order_id=order.id)
    except Exception as e:
        print(f"[miniapp_create_stars_order] create_heleket_invoice failed: {e}")
        raise HTTPException(status_code=502, detail="Unable to create payment link")

    if not invoice_url:
        raise HTTPException(status_code=502, detail="Unable to create payment link")

    return {
        "orderId": order.id,
        "paymentType": "USDT",
        "status": order.status.value,
        "starsAmount": payload.stars_amount,
        "toUsername": to_username,
        "priceUsdt": str(price),
        "invoiceUrl": invoice_url,
        "expiresInSeconds": 1800,
    }


@router.post("/miniapp/stars/quote")
async def miniapp_get_stars_quote(
    payload: MiniAppStarsQuotePayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    payment_type = PaymentType.TON if payload.payment_method == "TON" else PaymentType.USDT

    if payment_type == PaymentType.TON:
        try:
            price = await calculate_star_price_in_ton(payload.stars_amount)
        except Exception as e:
            print(f"[miniapp_get_stars_quote] TON price fallback used: {e}")
            price = (
                Decimal(payload.stars_amount) * Decimal("0.015") * Decimal("1.14")
            ).quantize(Decimal("0.001"), rounding=ROUND_UP)
        return {
            "starsAmount": payload.stars_amount,
            "priceTon": str(price),
            "currency": "TON",
            "ok": True,
            "language": user.language.value.lower(),
        }

    price = (
        Decimal(payload.stars_amount) * Decimal("0.015") * Decimal("1.14")
    ).quantize(Decimal("0.01"), rounding=ROUND_UP)
    return {
        "starsAmount": payload.stars_amount,
        "priceUsdt": str(price),
        "currency": "USDT",
        "ok": True,
        "language": user.language.value.lower(),
    }


@router.post("/miniapp/sell-stars/order")
async def miniapp_create_sell_stars_order(
    payload: MiniAppSellStarsOrderPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()

    payout_usdt = await calculate_sell_stars_payout_in_usdt(payload.stars_amount)
    order = await create_sell_star_order(
        session=session,
        user_id=user.id,
        stars_amount=payload.stars_amount,
        payout_usdt=payout_usdt,
    )

    if not bot:
        await delete_sell_star_order(session, order.id, user.id)
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")

    try:
        invoice_url = await bot.create_invoice_link(
            title=t(lang, "sell_stars.invoice_title"),
            description=t(lang, "sell_stars.invoice_description"),
            payload=f"sellstars:{order.id}",
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=t(lang, "sell_stars.invoice_label"),
                    amount=payload.stars_amount,
                )
            ],
        )
    except Exception as exc:
        await delete_sell_star_order(session, order.id, user.id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not invoice_url:
        await delete_sell_star_order(session, order.id, user.id)
        raise HTTPException(status_code=502, detail="Unable to create sell stars invoice")

    return {
        "orderId": order.id,
        "starsAmount": payload.stars_amount,
        "payoutUsdt": str(payout_usdt),
        "payoutTon": str(payout_usdt),
        "status": order.status.value,
        "invoiceUrl": invoice_url,
        "expiresInSeconds": 1800,
    }


@router.post("/miniapp/sell-stars/quote")
async def miniapp_get_sell_stars_quote(
    payload: MiniAppSellStarsQuotePayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    payout_usdt = await calculate_sell_stars_payout_in_usdt(payload.stars_amount)
    return {
        "starsAmount": payload.stars_amount,
        "payoutUsdt": str(payout_usdt),
        "payoutTon": str(payout_usdt),
        "currency": "USDT",
        "ok": True,
        "language": user.language.value.lower(),
    }


@router.post("/miniapp/sell-stars/pending")
async def miniapp_get_pending_sell_stars_orders(
    payload: MiniAppAuthPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    await expire_pending_sell_star_orders(session, user.id)
    result = await session.execute(
        select(SellStarOrder)
        .where(
            SellStarOrder.user_id == user.id,
            SellStarOrder.status == SellStarOrderStatus.PENDING,
        )
        .order_by(SellStarOrder.created_at.desc())
    )
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "orderId": order.id,
                "starsAmount": order.stars_amount,
                "payoutUsdt": str(order.payout_ton),
                "payoutTon": str(order.payout_ton),
                "status": order.status.value,
                "createdAt": order.created_at.isoformat() if order.created_at else None,
                "expiresInSeconds": get_remaining_seconds(order.created_at),
            }
            for order in orders
        ]
    }


@router.post("/miniapp/sell-stars/invoice")
async def miniapp_get_sell_stars_invoice_link(
    payload: MiniAppSellStarsInvoicePayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()

    order = await get_sell_star_order_by_id(session, payload.order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(
            status_code=404, detail=t(lang, "sell_stars.order_not_found")
        )
    if order.status != SellStarOrderStatus.PENDING:
        raise HTTPException(
            status_code=400, detail=t(lang, "sell_stars.order_not_pending")
        )
    if is_expired(order.created_at):
        raise HTTPException(
            status_code=400, detail=t(lang, "sell_stars.order_not_pending")
        )

    if not bot:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")

    invoice_url = await bot.create_invoice_link(
        title=t(lang, "sell_stars.invoice_title"),
        description=t(lang, "sell_stars.invoice_description"),
        payload=f"sellstars:{order.id}",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=t(lang, "sell_stars.invoice_label"), amount=order.stars_amount
            )
        ],
    )
    return {"orderId": order.id, "invoiceUrl": invoice_url}


@router.post("/miniapp/sell-stars/cancel")
async def miniapp_cancel_sell_stars_order(
    payload: MiniAppSellStarsCancelPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)

    order = await get_sell_star_order_by_id(session, payload.order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != SellStarOrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    cancelled = await cancel_sell_star_order(session, payload.order_id, user.id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    return {"ok": True, "orderId": payload.order_id}


@router.post("/miniapp/premium/order")
async def miniapp_create_premium_order(
    payload: MiniAppPremiumOrderPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, tg_user = await get_authenticated_db_user(session, payload.init_data)

    if payload.for_self:
        to_username = tg_user.get("username")
    else:
        to_username = (payload.to_username or "").strip().lstrip("@")

    if not to_username:
        raise HTTPException(status_code=400, detail="Target username is required")

    memo = generate_memo()
    payment_type = (
        PaymentType.TON if payload.payment_method == "TON" else PaymentType.USDT
    )

    if payment_type == PaymentType.TON:
        try:
            price = await calculate_premium_price_in_ton(payload.months)
        except Exception as e:
            print(f"[miniapp_create_premium_order] TON price fallback used: {e}")
            base_price = PREMIUM_PRICES_USD[payload.months]
            price = (base_price * Decimal("1.05")).quantize(
                Decimal("0.001"), rounding=ROUND_UP
            )
    else:
        base_price = PREMIUM_PRICES_USD[payload.months]
        price = (base_price * Decimal("1.05")).quantize(
            Decimal("0.01"), rounding=ROUND_UP
        )

    try:
        order = await create_order(
            session=session,
            user_id=user.id,
            to_username=to_username,
            stars=None,
            premium_months=payload.months,
            price_ton=price if payment_type == PaymentType.TON else None,
            price_usdt=price if payment_type == PaymentType.USDT else None,
            memo=memo,
            payment_type=payment_type,
            order_type=OrderType.PREMIUM,
        )
    except Exception as e:
        print(f"[miniapp_create_premium_order] create_order failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save order")

    if payment_type == PaymentType.TON:
        tonkeeper_links = build_tonkeeper_links(price, memo)
    return {
        "orderId": order.id,
        "paymentType": "TON",
        "status": order.status.value,
        "months": payload.months,
        "toUsername": to_username,
        "priceTon": str(price),
            "walletAddress": TON_WALLET_ADDRESS,
            "memo": memo,
            **tonkeeper_links,
            "expiresInSeconds": 1800,
        }

    try:
        invoice_url = await create_heleket_invoice(amount_usd=price, order_id=order.id)
    except Exception as e:
        print(f"[miniapp_create_premium_order] create_heleket_invoice failed: {e}")
        raise HTTPException(status_code=502, detail="Unable to create payment link")

    if not invoice_url:
        raise HTTPException(status_code=502, detail="Unable to create payment link")

    return {
        "orderId": order.id,
        "paymentType": "USDT",
        "status": order.status.value,
        "months": payload.months,
        "toUsername": to_username,
        "priceUsdt": str(price),
        "invoiceUrl": invoice_url,
        "expiresInSeconds": 1800,
    }


@router.post("/miniapp/orders/pending")
async def miniapp_get_pending_orders(
    payload: MiniAppPendingOrdersPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)

    statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING]
    query = select(Order).where(Order.user_id == user.id, Order.status.in_(statuses))

    if payload.order_type == "stars":
        query = query.where(Order.order_type == OrderType.STARS)
    elif payload.order_type == "premium":
        query = query.where(Order.order_type == OrderType.PREMIUM)

    query = query.order_by(Order.created_at.desc())
    result = await session.execute(query)
    orders = result.scalars().all()

    items = []
    now = datetime.now(timezone.utc)
    for order in orders:
        remaining_seconds = 1800
        if order.created_at:
            elapsed = int((now - order.created_at).total_seconds())
            remaining_seconds = max(0, 1800 - elapsed)

        item = {
            "orderId": order.id,
            "status": order.status.value,
            "orderType": order.order_type.value,
            "paymentType": order.payment_type.value,
            "toUsername": order.to_username,
            "starsAmount": order.stars_amount,
            "months": order.premium_months,
            "priceTon": str(order.price_ton) if order.price_ton is not None else None,
            "priceUsdt": (
                str(order.price_usdt) if order.price_usdt is not None else None
            ),
            "memo": order.memo,
            "walletAddress": (
                TON_WALLET_ADDRESS if order.payment_type == PaymentType.TON else None
            ),
            "createdAt": order.created_at.isoformat() if order.created_at else None,
            "expiresInSeconds": remaining_seconds,
        }
        if order.payment_type == PaymentType.TON and order.price_ton is not None:
            item.update(build_tonkeeper_links(order.price_ton, order.memo))
        items.append(item)

    return {"orders": items}


@router.post("/miniapp/payment/confirm")
async def miniapp_confirm_payment(
    payload: MiniAppPaymentConfirmPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)

    order_result = await session.execute(
        select(Order).where(Order.id == payload.order_id, Order.user_id == user.id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    lang = await get_lang(user.telegram_id)
    key = (
        "buy_tg_premium.confirm_payment"
        if order.order_type == OrderType.PREMIUM
        else "buy_stars.confirm_payment"
    )
    return {"ok": True, "message": t(lang, key)}


@router.post("/miniapp/order/cancel")
async def miniapp_cancel_order(
    payload: MiniAppOrderCancelPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)

    order_result = await session.execute(
        select(Order).where(Order.id == payload.order_id, Order.user_id == user.id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in {OrderStatus.PENDING, OrderStatus.PROCESSING}:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    order.status = OrderStatus.CANCELLED
    await session.commit()

    return {"ok": True}


@router.post("/miniapp/order/payment-link")
async def miniapp_get_order_payment_link(
    payload: MiniAppOrderPaymentLinkPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)

    order_result = await session.execute(
        select(Order).where(Order.id == payload.order_id, Order.user_id == user.id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {OrderStatus.PENDING, OrderStatus.PROCESSING}:
        raise HTTPException(status_code=400, detail="Order cannot be paid")

    if order.payment_type == PaymentType.TON:
        if order.price_ton is None:
            raise HTTPException(status_code=400, detail="Order cannot be paid")
        return {
            "paymentType": "TON",
            "walletAddress": TON_WALLET_ADDRESS,
            "memo": order.memo,
            **build_tonkeeper_links(order.price_ton, order.memo),
        }

    if order.price_usdt is None:
        raise HTTPException(status_code=400, detail="Order cannot be paid")

    invoice_url = await create_heleket_invoice(
        amount_usd=order.price_usdt, order_id=order.id
    )
    if not invoice_url:
        raise HTTPException(status_code=502, detail="Unable to create payment link")

    return {
        "paymentType": "USDT",
        "invoiceUrl": invoice_url,
    }


@router.post("/miniapp/gift-promo")
async def miniapp_gift_promo(
    payload: MiniAppAuthPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()
    return {
        "lang": lang,
        "captionHtml": t(lang, "menu.gift_promo"),
    }


@router.post("/miniapp/profile")
async def miniapp_profile(
    payload: MiniAppAuthPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()
    stats = await get_profile_stats(session, user)

    referral_link = f"https://t.me/VozikStarsBot?start={user.telegram_id}"
    commission = Decimal(user.referral_commission or Decimal("0.1")) * Decimal("100")

    return {
        "telegramId": user.telegram_id,
        "username": user.username,
        "language": lang,
        "supportUrl": SUPPORT_URL,
        "referralLink": referral_link,
        "referralCommissionPercent": format_decimal(commission, places=2),
        "referralCount": user.referral_count or 0,
        "activeReferralCount": user.active_referral_count or 0,
        "balanceUsdt": format_decimal(user.balance, places=2),
        "totalEarnedUsdt": format_decimal(user.total_earned, places=2),
        "referralEarnedUsdt": stats["referralEarnedUsdt"],
        "totalOrdersCount": stats["totalOrdersCount"],
        "purchasedStarsTotal": stats["purchasedStarsTotal"],
        "premiumMonthsTotal": stats["premiumMonthsTotal"],
        "exchangedStarsTotal": stats["exchangedStarsTotal"],
        "receivedUsdtTotal": stats["receivedUsdtTotal"],
        "scorePoints": stats["scorePoints"],
        "outperformPercent": stats["outperformPercent"],
        "savedTonWallet": user.default_ton_wallet,
        "minWithdrawalUsdt": "1",
    }


@router.post("/miniapp/wallet/set")
async def miniapp_set_wallet(
    payload: MiniAppWalletSetPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()

    wallet = (payload.wallet or "").strip()
    if not wallet:
        raise HTTPException(status_code=400, detail=t(lang, "withdrawal.wallet"))
    try:
        wallet = normalize_ton_wallet(wallet)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=t(lang, "withdrawal.invalid_wallet")
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    await set_user_default_ton_wallet(session, user, wallet)
    return {
        "ok": True,
        "wallet": wallet,
        "message": t(lang, "withdrawal.wallet_saved"),
    }


@router.post("/miniapp/withdraw")
async def miniapp_withdraw(
    payload: MiniAppWithdrawPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    lang = user.language.value.lower()

    amount = Decimal(payload.amount)
    if amount < Decimal("1"):
        raise HTTPException(status_code=400, detail=t(lang, "withdrawal.not_enough"))

    if amount > Decimal(user.balance or 0):
        raise HTTPException(status_code=400, detail=t(lang, "withdrawal.not_enough_2"))

    wallet = (payload.wallet or user.default_ton_wallet or "").strip()
    if not wallet:
        raise HTTPException(status_code=400, detail=t(lang, "withdrawal.wallet"))
    try:
        wallet = normalize_ton_wallet(wallet)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=t(lang, "withdrawal.invalid_wallet")
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    await set_user_default_ton_wallet(session, user, wallet)

    try:
        withdrawal = await create_withdrawal_request(session, user.id, amount, wallet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if bot:
        try:
            await notify_admins_about_withdrawal(bot, session, user, withdrawal)
        except TelegramForbiddenError:
            pass
        except Exception:
            pass

    return {
        "ok": True,
        "message": t(lang, "withdrawal.sent_info"),
        "withdrawalId": withdrawal.id,
        "status": "PENDING",
    }


@router.post("/miniapp/language")
async def miniapp_get_language(
    payload: MiniAppAuthPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    return {
        "language": user.language.value.lower(),
        "availableLanguages": ["en", "ru", "ua"],
    }


@router.post("/miniapp/language/set")
async def miniapp_set_language(
    payload: MiniAppLanguageSetPayload,
    session: AsyncSession = Depends(get_async_session),
):
    user, _ = await get_authenticated_db_user(session, payload.init_data)
    language = payload.language.lower()

    await set_user_language(session, user.telegram_id, Language(language.upper()))

    return {
        "ok": True,
        "language": language,
        "message": t(language, "language.changed"),
    }
