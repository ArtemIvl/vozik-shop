import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from db.session import SessionLocal
from db.models.sell_star_order import SellStarOrderStatus
from keyboards.menu_keyboard import back_to_menu_keyboard
from keyboards.sell_stars_keyboard import sell_stars_quote_keyboard
from requests.sell_star_order_requests import (
    create_sell_star_order,
    credit_user_balance_from_sell,
    get_sell_star_order_by_id,
    mark_sell_star_order_paid,
)
from requests.user_requests import get_user_by_telegram_id
from services.localization import get_lang, t
from services.payment import calculate_sell_stars_payout_in_usdt

router = Router()

SELL_STARS_MIN_AMOUNT = 50
SELL_ORDER_PAYLOAD_PREFIX = "sellstars"
INVOICE_TIMEOUT_SECONDS = 30


def register_sell_stars_handlers(dp) -> None:
    dp.include_router(router)


class SellStarsState(StatesGroup):
    waiting_for_amount = State()


def _build_sell_payload(order_id: int) -> str:
    return f"{SELL_ORDER_PAYLOAD_PREFIX}:{order_id}"


def _parse_sell_payload(payload: str) -> int | None:
    if not payload or not payload.startswith(f"{SELL_ORDER_PAYLOAD_PREFIX}:"):
        return None
    _, order_id_str = payload.split(":", 1)
    if not order_id_str.isdigit():
        return None
    return int(order_id_str)


async def _delete_invoice_if_still_pending(
    bot, chat_id: int, message_id: int, order_id: int
) -> None:
    await asyncio.sleep(INVOICE_TIMEOUT_SECONDS)
    try:
        async with SessionLocal() as session:
            order = await get_sell_star_order_by_id(session, order_id)
            if not order or order.status != SellStarOrderStatus.PENDING:
                return
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        return


@router.callback_query(F.data == "sell_stars")
async def start_sell_stars(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await state.set_state(SellStarsState.waiting_for_amount)
    await callback.message.edit_text(
        t(lang, "sell_stars.amount_prompt"),
        parse_mode="HTML",
        reply_markup=back_to_menu_keyboard(lang),
    )


@router.message(SellStarsState.waiting_for_amount)
async def handle_sell_stars_amount(message: Message, state: FSMContext) -> None:
    lang = await get_lang(message.from_user.id)
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(
            t(lang, "sell_stars.invalid_amount"),
            reply_markup=back_to_menu_keyboard(lang),
        )
        return

    stars_amount = int(text)
    if stars_amount < SELL_STARS_MIN_AMOUNT:
        await message.answer(
            t(lang, "sell_stars.invalid_amount"),
            reply_markup=back_to_menu_keyboard(lang),
        )
        return

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(
                t(lang, "withdrawal.not_found"),
                reply_markup=back_to_menu_keyboard(lang),
            )
            return
        payout_usdt = await calculate_sell_stars_payout_in_usdt(stars_amount)
        order = await create_sell_star_order(
            session=session,
            user_id=user.id,
            stars_amount=stars_amount,
            payout_usdt=payout_usdt,
        )

    await state.clear()
    await message.answer(
        (
            f"{t(lang, 'sell_stars.quote_title')}\n\n"
            f"{t(lang, 'sell_stars.quote_stars')} <b>{stars_amount}</b> ⭐️\n"
            f"{t(lang, 'sell_stars.quote_payout')} <b>{payout_usdt}</b> USDT\n\n"
            f"{t(lang, 'sell_stars.quote_info')}"
        ),
        parse_mode="HTML",
        reply_markup=sell_stars_quote_keyboard(lang, order.id, stars_amount),
    )


@router.callback_query(F.data.startswith("sell_stars_pay_"))
async def send_sell_stars_invoice(callback: CallbackQuery) -> None:
    lang = await get_lang(callback.from_user.id)
    try:
        order_id = int(callback.data.split("_")[-1])
    except (TypeError, ValueError):
        await callback.answer(t(lang, "sell_stars.order_not_found"), show_alert=True)
        return

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        order = await get_sell_star_order_by_id(session, order_id)

    if not user or not order or order.user_id != user.id:
        await callback.answer(t(lang, "sell_stars.order_not_found"), show_alert=True)
        return

    if order.status != SellStarOrderStatus.PENDING:
        await callback.answer(t(lang, "sell_stars.order_not_pending"), show_alert=True)
        return

    sent_invoice = await callback.message.answer_invoice(
        title=t(lang, "sell_stars.invoice_title"),
        description=t(lang, "sell_stars.invoice_description"),
        payload=_build_sell_payload(order.id),
        currency="XTR",
        prices=[
            LabeledPrice(
                label=t(lang, "sell_stars.invoice_label"), amount=order.stars_amount
            )
        ],
    )
    asyncio.create_task(
        _delete_invoice_if_still_pending(
            bot=callback.bot,
            chat_id=sent_invoice.chat.id,
            message_id=sent_invoice.message_id,
            order_id=order.id,
        )
    )
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery) -> None:
    order_id = _parse_sell_payload(query.invoice_payload)
    if order_id is None:
        await query.answer(ok=True)
        return

    lang = await get_lang(query.from_user.id)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, query.from_user.id)
        order = await get_sell_star_order_by_id(session, order_id)

    valid = bool(
        user
        and order
        and order.user_id == user.id
        and order.status == SellStarOrderStatus.PENDING
        and order.stars_amount == query.total_amount
        and query.currency == "XTR"
    )
    if not valid:
        await query.answer(
            ok=False, error_message=t(lang, "sell_stars.precheckout_error")
        )
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_sell_stars_payment(message: Message) -> None:
    payment = message.successful_payment
    order_id = _parse_sell_payload(payment.invoice_payload or "")
    if order_id is None:
        return

    lang = await get_lang(message.from_user.id)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        order = await get_sell_star_order_by_id(session, order_id)
        if not user or not order or order.user_id != user.id:
            await message.answer(
                t(lang, "sell_stars.order_not_found"),
                reply_markup=back_to_menu_keyboard(lang),
            )
            return

        updated = await mark_sell_star_order_paid(
            session=session,
            order_id=order.id,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            provider_payment_charge_id=payment.provider_payment_charge_id,
        )
        if not updated:
            await message.answer(
                t(lang, "sell_stars.already_processed"),
                reply_markup=back_to_menu_keyboard(lang),
            )
            return

        user = await credit_user_balance_from_sell(session, user.id, order.payout_ton)

    await message.answer(
        (
            f"{t(lang, 'sell_stars.payment_success')}\n\n"
            f"{t(lang, 'sell_stars.quote_stars')} <b>{order.stars_amount}</b> ⭐️\n"
            f"{t(lang, 'sell_stars.quote_payout')} <b>{order.payout_ton}</b> USDT\n"
            f"{t(lang, 'profile.balance')} <b>{user.balance:.2f}</b> USDT"
        ),
        parse_mode="HTML",
        reply_markup=back_to_menu_keyboard(lang),
    )
