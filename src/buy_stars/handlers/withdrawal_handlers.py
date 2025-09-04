from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from decimal import Decimal
from db.session import SessionLocal
from requests.user_requests import get_user_by_telegram_id, get_all_admins
from requests.withdrawal_requests import create_withdrawal_request
from keyboards.admin_keyboards import confirm_withdraw_keyboard
from keyboards.withdraw_keyboard import back_to_profile_keyboard
from services.localization import t, get_lang

router = Router()

def register_withdrawal_handlers(dp) -> None:
    dp.include_router(router)

class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_wallet = State()

@router.callback_query(F.data == "withdraw_referral")
async def start_withdraw(callback: CallbackQuery, state: FSMContext):
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        lang = await get_lang(callback.from_user.id)
        if not user:
            await callback.answer(t(lang, 'withdrawal.not_found'), show_alert=True)
            return

        if user.referral_balance < Decimal("0.5"):
            await callback.answer(t(lang, 'withdrawal.not_enough'), show_alert=True)
            return

        await callback.message.edit_text(t(lang, 'withdrawal.amount'), reply_markup=back_to_profile_keyboard(lang))
        await state.set_state(WithdrawState.waiting_for_amount)

@router.message(WithdrawState.waiting_for_amount)
async def ask_wallet(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    try:
        amount = Decimal(message.text)
    except Exception:
        await message.answer(t(lang, 'withdrawal.invalid_amount'))
        return

    if amount < Decimal("0.5"):
        await message.answer(t(lang, 'withdrawal.not_enough'))
        return

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if amount > user.referral_balance:
            await message.answer(t(lang, 'withdrawal.not_enough_2'))
            return

    await state.update_data(amount=amount)
    await state.set_state(WithdrawState.waiting_for_wallet)
    await message.answer(t(lang, 'withdrawal.wallet'))

@router.message(WithdrawState.waiting_for_wallet)
async def create_withdraw_callback(message: Message, state: FSMContext):
    wallet = message.text.strip()
    data = await state.get_data()
    amount = data["amount"]
    lang = await get_lang(message.from_user.id)

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        withdrawal = await create_withdrawal_request(session, user.id, amount, wallet)

        admins = await get_all_admins(session)
        for admin in admins:
            await message.bot.send_message(
                admin.telegram_id,
                f"🌐 Новая заявка на вывод:\n"
                f"👤 @{user.username} | {user.telegram_id}\n"
                f"💸 Сумма: {amount} TON\n"
                f"💳 Кошелёк: <code>{wallet}</code>\n"
                f"ID заявки: {withdrawal.id}",
                parse_mode="HTML",
                reply_markup=confirm_withdraw_keyboard(withdrawal.id)
            )

    await message.answer(
        t(lang, 'withdrawal.sent_info'),
        parse_mode="HTML",
        reply_markup=back_to_profile_keyboard(lang),
    )
    await state.clear()
