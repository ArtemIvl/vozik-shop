from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from decimal import Decimal
from db.session import SessionLocal
from requests.user_requests import get_user_by_telegram_id, set_user_default_ton_wallet
from requests.withdrawal_requests import create_withdrawal_request
from keyboards.withdraw_keyboard import back_to_profile_keyboard, saved_wallet_keyboard
from services.localization import t, get_lang
from services.ton_wallets import normalize_ton_wallet
from services.withdrawal_flow import notify_admins_about_withdrawal

router = Router()


def register_withdrawal_handlers(dp) -> None:
    dp.include_router(router)


class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_wallet = State()
    waiting_for_wallet_save = State()


async def finalize_withdrawal(
    message: Message,
    telegram_id: int,
    amount: Decimal,
    wallet: str,
    lang: str,
    state: FSMContext,
):
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if not user:
            await message.answer(t(lang, "withdrawal.not_found"))
            await state.clear()
            return
        await set_user_default_ton_wallet(session, user, wallet)
        withdrawal = await create_withdrawal_request(session, user.id, amount, wallet)
        await notify_admins_about_withdrawal(message.bot, session, user, withdrawal)

    await message.answer(
        t(lang, "withdrawal.sent_info"),
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard(lang),
    )
    await state.clear()


@router.callback_query(F.data == "withdraw_referral")
async def start_withdraw(callback: CallbackQuery, state: FSMContext):
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        lang = await get_lang(callback.from_user.id)
        if not user:
            await callback.answer(t(lang, "withdrawal.not_found"), show_alert=True)
            return

        if user.balance < Decimal("1"):
            await callback.answer(t(lang, "withdrawal.not_enough"), show_alert=True)
            return

        await callback.message.edit_text(
            t(lang, "withdrawal.amount"), reply_markup=back_to_profile_keyboard(lang)
        )
        await state.set_state(WithdrawState.waiting_for_amount)


@router.callback_query(F.data == "save_wallet")
async def start_save_wallet(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    await state.set_state(WithdrawState.waiting_for_wallet_save)
    await callback.message.edit_text(
        t(lang, "withdrawal.wallet_change"),
        reply_markup=back_to_profile_keyboard(lang),
    )
    await callback.answer()


@router.message(WithdrawState.waiting_for_amount)
async def ask_wallet(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    try:
        amount = Decimal(message.text)
    except Exception:
        await message.answer(t(lang, "withdrawal.invalid_amount"))
        return

    if amount < Decimal("1"):
        await message.answer(t(lang, "withdrawal.not_enough"))
        return

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(t(lang, "withdrawal.not_found"))
            await state.clear()
            return
        if amount > user.balance:
            await message.answer(t(lang, "withdrawal.not_enough_2"))
            return
        saved_wallet = user.default_ton_wallet

    await state.update_data(amount=amount)
    await state.set_state(WithdrawState.waiting_for_wallet)
    if saved_wallet:
        await state.update_data(saved_wallet=saved_wallet)
        await message.answer(
            f"{t(lang, 'withdrawal.saved_wallet')}\n<code>{saved_wallet}</code>\n\n{t(lang, 'withdrawal.wallet_saved_prompt')}",
            reply_markup=saved_wallet_keyboard(lang),
            parse_mode="HTML",
        )
        return

    await message.answer(t(lang, "withdrawal.wallet"))


@router.callback_query(
    WithdrawState.waiting_for_wallet, F.data == "withdraw_use_saved_wallet"
)
async def use_saved_wallet(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    saved_wallet = data.get("saved_wallet")
    lang = await get_lang(callback.from_user.id)

    if not amount or not saved_wallet:
        await callback.answer(t(lang, "withdrawal.wallet"), show_alert=True)
        return

    await callback.answer()
    await finalize_withdrawal(
        callback.message, callback.from_user.id, amount, saved_wallet, lang, state
    )


@router.callback_query(
    WithdrawState.waiting_for_wallet, F.data == "withdraw_change_wallet"
)
async def change_saved_wallet(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        t(lang, "withdrawal.wallet_change"),
        reply_markup=back_to_profile_keyboard(lang),
    )


@router.message(WithdrawState.waiting_for_wallet)
async def create_withdraw_callback(message: Message, state: FSMContext):
    wallet = message.text.strip()
    data = await state.get_data()
    amount = data["amount"]
    lang = await get_lang(message.from_user.id)
    try:
        wallet = normalize_ton_wallet(wallet)
    except ValueError:
        await message.answer(t(lang, "withdrawal.invalid_wallet"))
        return
    except RuntimeError as exc:
        await message.answer(str(exc))
        return
    await finalize_withdrawal(
        message, message.from_user.id, amount, wallet, lang, state
    )


@router.message(WithdrawState.waiting_for_wallet_save)
async def save_wallet_callback(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    wallet = message.text.strip()
    try:
        wallet = normalize_ton_wallet(wallet)
    except ValueError:
        await message.answer(t(lang, "withdrawal.invalid_wallet"))
        return
    except RuntimeError as exc:
        await message.answer(str(exc))
        return

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(t(lang, "withdrawal.not_found"))
            await state.clear()
            return
        await set_user_default_ton_wallet(session, user, wallet)

    await message.answer(
        t(lang, "withdrawal.wallet_saved"),
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard(lang),
    )
    await state.clear()
