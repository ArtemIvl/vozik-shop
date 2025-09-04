from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.buy_stars_keyboard import payment_method_keyboard, open_tonkeeper_keyboard, heleket_invoice_keyboard, stars_username_keyboard
from keyboards.menu_keyboard import back_to_menu_keyboard
from aiogram.fsm.state import State, StatesGroup
from services.payment import generate_memo, calculate_star_price_in_ton
from services.heleket import create_heleket_invoice
from requests.order_requests import create_order
from db.session import SessionLocal
from requests.user_requests import get_user_by_telegram_id
from db.models.order import PaymentType, OrderType
from config import TON_WALLET_ADDRESS
from services.localization import t, get_lang

router = Router()

def register_buy_stars_handlers(dp) -> None:
    dp.include_router(router)

class BuyStarsState(StatesGroup):
    waiting_for_username = State()
    waiting_for_username_choice = State()
    waiting_for_amount = State()
    waiting_for_payment_method = State()
    waiting_for_confirmation = State()

@router.callback_query(F.data == "buy_stars")
async def start_buy(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    username = callback.from_user.username
    lang = await get_lang(callback.from_user.id)

    await state.set_state(BuyStarsState.waiting_for_username_choice)
    await callback.message.edit_text(t(lang, "buy_stars.username"), reply_markup=stars_username_keyboard(lang, username))

@router.callback_query(BuyStarsState.waiting_for_username_choice, F.data == "stars_for_self")
async def handle_self_username(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    lang = await get_lang(callback.from_user.id)

    await state.update_data(to_username=username)
    await state.set_state(BuyStarsState.waiting_for_amount)
    await callback.message.edit_text(t(lang, "buy_stars.stars_amount"), reply_markup=back_to_menu_keyboard(lang))


@router.callback_query(BuyStarsState.waiting_for_username_choice, F.data == "stars_for_other")
async def ask_other_username(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(callback.from_user.id)
    await state.set_state(BuyStarsState.waiting_for_username)
    await callback.message.edit_text(t(lang, "buy_stars.enter_username"), reply_markup=back_to_menu_keyboard(lang))


@router.message(BuyStarsState.waiting_for_username)
async def save_friend_username(message: Message, state: FSMContext) -> None:
    username = message.text.strip().lstrip("@")
    lang = await get_lang(message.from_user.id)
    if not username:
        await message.answer(t(lang, "buy_stars.invalid_username"), reply_markup=back_to_menu_keyboard(lang))
        return

    await state.update_data(to_username=username)
    await state.set_state(BuyStarsState.waiting_for_amount)
    await message.answer(t(lang, "buy_stars.stars_amount"), reply_markup=back_to_menu_keyboard(lang))


@router.message(BuyStarsState.waiting_for_amount)
async def ask_payment_method(message: Message, state: FSMContext) -> None:
    lang = await get_lang(message.from_user.id)
    if not message.text.isdigit() or int(message.text) < 50:
        await message.answer(t(lang, "buy_stars.invalid_amount"), reply_markup=back_to_menu_keyboard(lang))
        return

    await state.update_data(stars=int(message.text))
    await state.set_state(BuyStarsState.waiting_for_payment_method)
    await message.answer(t(lang, "buy_stars.payment_method"), reply_markup=payment_method_keyboard(lang))

@router.callback_query(BuyStarsState.waiting_for_payment_method, F.data.in_(["buy_for_ton", "buy_for_usdt"]))
async def handle_payment_choice(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    to_username = data["to_username"]
    stars = data["stars"]
    payment_type = PaymentType.TON if callback.data == "buy_for_ton" else PaymentType.USDT
    lang = await get_lang(callback.from_user.id)

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        memo = generate_memo()
        if payment_type == PaymentType.TON:
            price = await calculate_star_price_in_ton(stars)
        else:
            price = round(stars * 0.015 * float(1.14), 2)

        order = await create_order(
            session=session,
            user_id=user.id,
            to_username=to_username,
            stars=stars,
            premium_months=None,
            price_ton=price if payment_type == PaymentType.TON else None,
            price_usdt=price if payment_type == PaymentType.USDT else None,
            memo=memo,
            payment_type=payment_type,
            order_type=OrderType.STARS
        )

    if payment_type == PaymentType.TON:
        msg = (
            f"<b>@{user.username}</b>, {t(lang, 'buy_stars.order_ton.valid_for')}\n\n"
            f"<b>{stars}</b> {t(lang, 'buy_stars.order_ton.stars_for')} @{to_username}\n\n"
            f"{t(lang, 'buy_stars.order_ton.details')}\n"
            f"{t(lang, 'buy_stars.order_ton.amount')} <code>{price}</code> <b>TON</b>\n"
            f"{t(lang, 'buy_stars.order_ton.address')} <code>{TON_WALLET_ADDRESS}</code>\n\n"
            f"{t(lang, 'buy_stars.order_ton.memo')}\n<code>{memo}</code>👈🏻\n\n"
            f"{t(lang, 'buy_stars.order_ton.info')}"
        )
        await state.set_state(BuyStarsState.waiting_for_confirmation)
        await callback.message.edit_text(msg, reply_markup=open_tonkeeper_keyboard(lang, price, memo), parse_mode='HTML')

    elif payment_type == PaymentType.USDT:
        invoice_url = await create_heleket_invoice(amount_usd=price, order_id=order.id)
        if invoice_url:
            msg = (
                f"<b>@{user.username}</b>, {t(lang, 'buy_stars.order_usd.valid_for')}\n\n"
                f"<b>{stars}</b> {t(lang, 'buy_stars.order_usd.stars_for')} @{to_username}\n\n"
                f"{t(lang, 'buy_stars.order_usd.info')}"
            )
            await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=heleket_invoice_keyboard(lang, invoice_url))
        else:
            await callback.message.answer(t(lang, 'buy_stars.error_3'), reply_markup=back_to_menu_keyboard(lang))


@router.callback_query(BuyStarsState.waiting_for_confirmation, F.data == "confirm_payment")
async def handle_confirm_payment(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await callback.message.answer(
        t(lang, "buy_stars.confirm_payment"),
        reply_markup=back_to_menu_keyboard(lang)
    )
