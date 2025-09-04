from db.session import SessionLocal
from aiogram import F, Router, types
from requests.withdrawal_requests import get_pending_withdrawals, get_withdrawal_by_id, approve_withdrawal, reject_withdrawal
from requests.user_requests import get_user_by_id
from aiogram.exceptions import TelegramForbiddenError
from keyboards.admin_keyboards import pending_withdraw_keyboard, withdraw_info_keyboard, confirm_withdraw_keyboard, reject_withdraw_keyboard
from pytz import timezone
from services.localization import t, get_lang

withdraw_admin_router = Router()

kyiv_tz = timezone("Europe/Kyiv")


@withdraw_admin_router.callback_query(F.data == "manage_withdrawals")
async def manage_withdrawals_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        withdrawals = await get_pending_withdrawals(session)
        await callback.message.edit_text(
            "Список выводов:",
            reply_markup=await pending_withdraw_keyboard(session, withdrawals, page=1),
        )


@withdraw_admin_router.callback_query(F.data.startswith("withdraw_page_"))
async def handle_withdraw_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split("_")[-1])
    async with SessionLocal() as session:
        withdrawals = await get_pending_withdrawals(session)
        await callback.message.edit_text(
            "Список выводов:",
            reply_markup=await pending_withdraw_keyboard(
                session, withdrawals, page=page
            ),
        )
        await callback.answer()


@withdraw_admin_router.callback_query(F.data.startswith("withdraw_info_"))
async def withdraw_info_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)
        text = (
            f"🌐 Заявка на вывод {withdrawal.id}:\n\n"
            f"👤 @{user.username} | {user.telegram_id}\n"
            f"💸 Сумма: {withdrawal.ton_amount} TON\n"
            f"💳 Кошелёк: <code>{withdrawal.ton_address}</code>\n"
            f"Рефералов: {user.referral_count}\n"
            f"Всего заработано с бота: {user.referral_total_earned}\n"
            f"Текущий баланс: {user.referral_balance}\n"
            f"Комиссия: {user.referral_commission * 100}%\n"
            f"Дата регистрации: {user.reg_date.astimezone(kyiv_tz).strftime('%d.%m.%Y')}"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=withdraw_info_keyboard(withdrawal.id),
        )

@withdraw_admin_router.callback_query(F.data.startswith("confirm_withdrawal_"))
async def confirm_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        "Вы уверены, что хотите подтвердить вывод?",
        reply_markup=confirm_withdraw_keyboard(withdrawal_id)
    )


@withdraw_admin_router.callback_query(F.data.startswith("confirm_final_"))
async def confirm_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await approve_withdrawal(session, withdrawal_id)
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)

        try:
            lang = await get_lang(user.telegram_id)
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=t(lang, 'withdrawal.confirmed'),
                parse_mode="HTML",
            )
        except TelegramForbiddenError:
            pass

        await callback.answer("Вывод подтвержден!", show_alert=True)
    withdrawals = await get_pending_withdrawals(session)
    await callback.message.edit_text(
        "Список выводов:",
        reply_markup=await pending_withdraw_keyboard(session, withdrawals, page=1),
    )

@withdraw_admin_router.callback_query(F.data.startswith("reject_final_"))
async def reject_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        "Вы уверены, что хотите отклонить вывод?",
        reply_markup=reject_withdraw_keyboard(withdrawal_id)
    )


@withdraw_admin_router.callback_query(F.data.startswith("reject_withdrawal_"))
async def reject_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await reject_withdrawal(session, withdrawal_id)
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        user = await get_user_by_id(session, withdrawal.user_id)

        try:
            lang = await get_lang(user.telegram_id)
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=t(lang, 'withdrawal.rejected'),
                parse_mode="HTML",
            )
        except TelegramForbiddenError:
            pass

        await callback.answer("Вывод отклонен!", show_alert=True)
        withdrawals = await get_pending_withdrawals(session)
    await callback.message.edit_text(
        "Список выводов:",
        reply_markup=await pending_withdraw_keyboard(session, withdrawals, page=1),
    )