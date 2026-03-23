from db.session import SessionLocal
from aiogram import F, Router, types
from requests.withdrawal_requests import get_pending_withdrawals, get_withdrawal_by_id, approve_withdrawal, reject_withdrawal_and_refund
from requests.user_requests import get_user_by_id
from aiogram.exceptions import TelegramForbiddenError
from keyboards.admin_keyboards import pending_withdraw_keyboard, withdraw_info_keyboard, confirm_withdraw_keyboard, reject_withdraw_keyboard
from db.models.withdrawal import WithdrawalStatus
from services.localization import t, get_lang
from services.ton_withdrawal import get_sender_usdt_balance, send_usdt_withdrawal
from services.withdrawal_flow import build_withdrawal_admin_message

withdraw_admin_router = Router()


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
        text = await build_withdrawal_admin_message(session, user, withdrawal)

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
        withdrawal = await get_withdrawal_by_id(session, withdrawal_id)
        if not withdrawal:
            await callback.answer("Заявка не найдена.", show_alert=True)
            return
        if withdrawal.status != WithdrawalStatus.PENDING:
            await callback.answer("Эта заявка уже обработана.", show_alert=True)
            return

        user = await get_user_by_id(session, withdrawal.user_id)
        try:
            available_balance = await get_sender_usdt_balance()
        except Exception as exc:
            await callback.answer(f"Не удалось проверить баланс USDT: {exc}", show_alert=True)
            return

        if available_balance < withdrawal.ton_amount:
            await callback.answer(
                f"Недостаточно USDT на кошельке бота. Доступно: {available_balance:.2f} USDT, требуется: {withdrawal.ton_amount:.2f} USDT.",
                show_alert=True,
            )
            return

        ok, details = await send_usdt_withdrawal(withdrawal.ton_address, withdrawal.ton_amount)

        if not ok:
            await callback.answer(f"Не удалось отправить USDT: {details}", show_alert=True)
            await callback.message.edit_text(
                await build_withdrawal_admin_message(session, user, withdrawal) + f"\n\n❌ Ошибка отправки: <code>{details}</code>",
                parse_mode="HTML",
                reply_markup=withdraw_info_keyboard(withdrawal.id),
            )
            return

        await approve_withdrawal(session, withdrawal_id)

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

@withdraw_admin_router.callback_query(F.data.startswith("reject_withdrawal_"))
async def reject_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        "Вы уверены, что хотите отклонить вывод?",
        reply_markup=reject_withdraw_keyboard(withdrawal_id)
    )


@withdraw_admin_router.callback_query(F.data.startswith("reject_final_"))
async def reject_withdrawal_callback(callback: types.CallbackQuery) -> None:
    withdrawal_id = int(callback.data.split("_")[2])
    async with SessionLocal() as session:
        await reject_withdrawal_and_refund(session, withdrawal_id)
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
