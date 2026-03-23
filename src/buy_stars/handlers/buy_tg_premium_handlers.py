from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.menu_keyboard import back_to_menu_keyboard
from keyboards.buy_stars_keyboard import (
    payment_method_keyboard,
    open_tonkeeper_keyboard,
    heleket_invoice_keyboard,
)
from keyboards.buy_tg_premium_keyboard import (
    premium_duration_keyboard,
    premium_username_keyboard,
)
from services.payment import generate_memo, calculate_premium_price_in_ton
from requests.order_requests import create_order
from requests.user_requests import get_user_by_telegram_id
from services.heleket import create_heleket_invoice
from services.localization import get_lang, t
from db.models.order import PaymentType, OrderType
from db.session import SessionLocal
from decimal import Decimal
from config import TON_WALLET_ADDRESS

router = Router()


def register_buy_tg_premium_handlers(dp) -> None:
    dp.include_router(router)


class BuyPremiumState(StatesGroup):
    waiting_for_username_choice = State()
    waiting_for_username = State()
    waiting_for_duration = State()
    waiting_for_payment_method = State()
    waiting_for_confirmation = State()


PREMIUM_PRICES_USD = {
    3: Decimal("12"),
    6: Decimal("16"),
    12: Decimal("29"),
}


@router.callback_query(F.data == "buy_tg_premium")
async def start_premium_by(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    username = callback.from_user.username

    await state.set_state(BuyPremiumState.waiting_for_username_choice)
    await callback.message.edit_text(
        t(lang, "buy_tg_premium.username"),
        reply_markup=premium_username_keyboard(lang, username),
    )


@router.callback_query(
    BuyPremiumState.waiting_for_username_choice, F.data == "premium_for_self"
)
async def handle_self_username(callback: CallbackQuery, state: FSMContext) -> None:
    username = callback.from_user.username
    lang = await get_lang(callback.from_user.id)

    await state.update_data(to_username=username)
    await state.set_state(BuyPremiumState.waiting_for_duration)
    await callback.message.edit_text(
        t(lang, "buy_tg_premium.duration"), reply_markup=premium_duration_keyboard(lang)
    )


@router.callback_query(
    BuyPremiumState.waiting_for_username_choice, F.data == "premium_for_other"
)
async def ask_other_username(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(callback.from_user.id)
    await state.set_state(BuyPremiumState.waiting_for_username)
    await callback.message.edit_text(
        t(lang, "buy_tg_premium.enter_username"),
        reply_markup=back_to_menu_keyboard(lang),
    )


@router.message(BuyPremiumState.waiting_for_username)
async def premium_entered_username(message: Message, state: FSMContext):
    username = message.text.lstrip("@").strip()
    lang = await get_lang(message.from_user.id)
    if not username:
        await message.answer(
            t(lang, "buy_tg_premium.invalid_username"),
            reply_markup=back_to_menu_keyboard(lang),
        )
        return

    await state.update_data(to_username=username)
    await state.set_state(BuyPremiumState.waiting_for_duration)
    await message.answer(
        t(lang, "buy_tg_premium.duration"), reply_markup=premium_duration_keyboard(lang)
    )


@router.callback_query(
    BuyPremiumState.waiting_for_duration, F.data.startswith("premium_months_")
)
async def premium_select_duration(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[-1])
    lang = await get_lang(callback.from_user.id)

    await state.update_data(months=months)
    await state.set_state(BuyPremiumState.waiting_for_payment_method)
    await callback.message.edit_text(
        t(lang, "buy_tg_premium.payment_method"),
        reply_markup=payment_method_keyboard(lang),
    )


@router.callback_query(
    BuyPremiumState.waiting_for_payment_method,
    F.data.in_(["buy_for_ton", "buy_for_usdt"]),
)
async def premium_handle_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_username = data["to_username"]
    months = data["months"]
    payment_type = (
        PaymentType.TON if callback.data == "buy_for_ton" else PaymentType.USDT
    )
    lang = await get_lang(callback.from_user.id)

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        memo = generate_memo()
        if payment_type == PaymentType.TON:
            price = await calculate_premium_price_in_ton(months)
        else:
            base_price = PREMIUM_PRICES_USD[months]
            price = base_price * Decimal("1.05")

        order = await create_order(
            session=session,
            user_id=user.id,
            to_username=to_username,
            stars=None,
            premium_months=months,
            price_ton=price if payment_type == PaymentType.TON else None,
            price_usdt=price if payment_type == PaymentType.USDT else None,
            memo=memo,
            payment_type=payment_type,
            order_type=OrderType.PREMIUM,
        )

    if payment_type == PaymentType.TON:
        msg = (
            f"<b>@{user.username}</b>, {t(lang, 'buy_tg_premium.order_ton.valid_for')}\n\n"
            f"{t(lang, 'buy_tg_premium.order_ton.premium_duration')} <b>{months}</b> {t(lang, 'buy_tg_premium.order_ton.premium_for')} @{to_username}\n\n"
            f"{t(lang, 'buy_tg_premium.order_for.details')}"
            f"{t(lang, 'buy_tg_premium.order_ton.amount')} <code>{price}</code> TON\n"
            f"{t(lang, 'buy_tg_premium.order_ton.address')} <code>{TON_WALLET_ADDRESS}</code>\n\n"
            f"{t(lang, 'buy_tg_premium.order_ton.memo')}\n<code>{memo}</code>👈🏻\n\n"
            f"{t(lang, 'buy_tg_premium.order_ton.info')}"
        )
        await state.set_state(BuyPremiumState.waiting_for_confirmation)
        await callback.message.answer(
            msg,
            reply_markup=open_tonkeeper_keyboard(lang, price, memo),
            parse_mode="HTML",
        )

    elif payment_type == PaymentType.USDT:
        invoice_url = await create_heleket_invoice(amount_usd=price, order_id=order.id)
        if invoice_url:
            msg = (
                f"<b>@{user.username}</b>, {t(lang, 'buy_tg_premium.order_usd.valid_for')}\n\n"
                f"{t(lang, 'buy_tg_premium.order_usd.premium_duration')} <b>{months}</b> {t(lang, 'buy_tg_premium.order_usd.premium_for')} @{to_username}\n\n"
                f"{t(lang, 'buy_tg_premium.order_usd.info')}"
            )
            await callback.message.answer(
                msg,
                parse_mode="HTML",
                reply_markup=heleket_invoice_keyboard(lang, invoice_url),
            )
        else:
            await callback.message.answer(
                t(lang, "buy_tg_premium.error_3"),
                reply_markup=back_to_menu_keyboard(lang),
            )


@router.callback_query(
    BuyPremiumState.waiting_for_confirmation, F.data == "confirm_payment"
)
async def handle_confirm_payment(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await callback.message.answer(
        t(lang, "buy_tg_premium.confirm_payment"),
        reply_markup=back_to_menu_keyboard(lang),
    )
