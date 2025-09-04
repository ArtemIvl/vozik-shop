from decimal import Decimal

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models.user import User
# from db.models.withdrawal import WithdrawalStatus
from db.session import SessionLocal
from keyboards.admin_keyboards import back_to_users_keyboard, manage_users_keyboard
from pytz import timezone

from requests.user_requests import (
    add_admin,
    ban_user,
    change_referral_commission,
    get_user_by_telegram_id,
    remove_admin,
    unban_user,
)

user_admin_router = Router()

kyiv_tz = timezone("Europe/Kyiv")

class AdminActions(StatesGroup):
    view_user = State()
    change_commission = State()
    set_commission_value = State()
    ban_user = State()
    unban_user = State()
    add_admin = State()
    remove_admin = State()


@user_admin_router.callback_query(F.data == "manage_users")
async def manage_users_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Управление пользователями:", reply_markup=manage_users_keyboard()
    )


@user_admin_router.callback_query(F.data == "view_user")
async def view_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.view_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите посмотреть:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.view_user, F.text.regexp(r"^\d+$"))
async def view_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    telegram_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            text, keyboard = await generate_detailed_user_text(user)
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            await state.clear()
        else:
            sent = await message.answer(
                "Пользователь не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "change_commission")
async def view_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.change_commission)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которому нужно поменять коммиссию:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.change_commission, F.text.regexp(r"^\d+$"))
async def view_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    telegram_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            await state.update_data(target_telegram_id=telegram_id)
            percent = round(float(user.referral_commission or 0) * 100, 2)
            sent = await message.answer(
                f"У пользователя @{user.username} сейчас установлена комиссия <b>{percent}%</b>.\n"
                "На какую её поменять? (от 0 до 1)",
                reply_markup=back_to_users_keyboard(),
                parse_mode="HTML"
            )
            await state.update_data(last_bot_message_id=sent.message_id)
            await state.set_state(AdminActions.set_commission_value)
        else:
            sent = await message.answer(
                "Пользователь не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.set_commission_value, F.text.regexp(r"^\d+(\.\d+)?$"))
async def set_commission(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    new_value = float(message.text)
    if new_value < 0 or new_value > 1:
        await message.answer("Введите корректное значение (от 0 до 1).")
        return

    data = await state.get_data()
    telegram_id = data.get("target_telegram_id")

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            await change_referral_commission(session, user, Decimal(new_value))
            await message.answer(f"✅ Комиссия для пользователя @{user.username} успешно изменена на {new_value * 100}%.", reply_markup=back_to_users_keyboard())
        else:
            await message.answer("Пользователь не найден.")

    await state.clear()

@user_admin_router.callback_query(F.data == "ban_user")
async def ban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.ban_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите забанить:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.ban_user, F.text.regexp(r"^\d+$"))
async def ban_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_banned:
                await message.answer(
                    "Пользователь уже забанен.", reply_markup=back_to_users_keyboard()
                )
                await state.clear()
                return
            await ban_user(session, user)
            await message.answer(
                f"Пользователь с ID {user_id} заблокирован.",
                reply_markup=back_to_users_keyboard(),
            )
            await state.clear()
        else:
            sent = await message.answer(
                "Пользоатель не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "unban_user")
async def unban_user_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.unban_user)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите разбанить:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.unban_user, F.text.regexp(r"^\d+$"))
async def unban_user_by_id(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_banned:
                await message.answer(
                    "Пользователь не заблокирован.",
                    reply_markup=back_to_users_keyboard(),
                )
                await state.clear()
                return
            await unban_user(session, user)
            await message.answer(
                f"Пользователь с ID {user_id} успешно разблокирован.",
                reply_markup=back_to_users_keyboard(),
            )
            await state.clear()
        else:
            sent = await message.answer(
                "Пользователь не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminActions.add_admin)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите сделать админом:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.add_admin, F.text.regexp(r"^\d+$"))
async def make_user_admin(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if user.is_admin:
                await message.answer(
                    "Пользователь уже администратор.",
                    reply_markup=back_to_users_keyboard(),
                )
                await state.clear()
                return
            await add_admin(session, user)
            await message.answer(
                f"Пользователь с ID {user_id} получил права администратора.",
                reply_markup=back_to_users_keyboard(),
            )
            await state.clear()
        else:
            sent = await message.answer(
                "Пользователь не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.callback_query(F.data == "remove_admin")
async def remove_admin_callback(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    await state.set_state(AdminActions.remove_admin)
    sent = await callback.message.edit_text(
        "Пожалуйста, отправьте телеграм айди пользователя, которого вы хотите удалить из админов:",
        reply_markup=back_to_users_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@user_admin_router.message(AdminActions.remove_admin, F.text.regexp(r"^\d+$"))
async def remove_user_admin(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    user_id = int(message.text)
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, user_id)
        if user:
            if not user.is_admin:
                await message.answer(
                    "Пользователь не администратор.",
                    reply_markup=back_to_users_keyboard(),
                )
                await state.clear()
                return
            await remove_admin(session, user)
            await message.answer(
                f"Пользователь с ID {user_id} был лишен прав администратора.",
                reply_markup=back_to_users_keyboard(),
            )
            await state.clear()
        else:
            sent = await message.answer(
                "Пользователь не найден. Попробуйте ещё раз:",
                reply_markup=back_to_users_keyboard(),
            )
            await state.update_data(last_bot_message_id=sent.message_id)


async def generate_detailed_user_text(user: User) -> tuple[str, types.InlineKeyboardMarkup]:
    # withdrawals = await get_completed_user_withdrawals(session, user.id)
    ref_balance_str = f"{user.referral_balance:.4f}" if user.referral_balance > 0 else "0.0"
    ref_total_earned_str = f"{user.referral_total_earned:.4f}" if user.referral_total_earned > 0 else "0.0"    
   
    text = (
        f"<b>Пользователь:</b>\n\n"
        f"ID: {user.telegram_id}\n"
        f"Username: @{user.username}\n"
        f"Админ? {'Да' if user.is_admin else 'Нет'}\n"
        f"Заблокирован? {'Да' if user.is_banned else 'Нет'}\n"
        f"Дата регистрации: {user.reg_date.astimezone(kyiv_tz).strftime('%d.%m.%Y')}\n\n"
        f"<b>Рефералы:</b>\n"
        f"У пользователя {user.referral_count} рефералов\n"
        f"Текущий баланс: {ref_balance_str}\n"
        f"Всего заработано: {ref_total_earned_str}\n"
        f"Текущая комиссия: {user.referral_commission}\n"
    )

    keyboard = back_to_users_keyboard()

    return text, keyboard