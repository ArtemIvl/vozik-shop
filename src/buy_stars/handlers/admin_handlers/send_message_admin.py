import asyncio
from datetime import datetime, timedelta
from pytz import timezone

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.admin_keyboards import (
    admin_back_keyboard,
    back_to_message_keyboard,
    time_choice_keyboard,
)
from services.broadcast import delayed_broadcast, send_broadcast

message_admin_router = Router()


class BroadcastState(StatesGroup):
    entering_message = State()
    choosing_time = State()
    waiting_to_send = State()


kyiv_tz = timezone("Europe/Kyiv")


@message_admin_router.callback_query(F.data == "send_message")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastState.entering_message)
    sent = await callback.message.edit_text(
        "Введите сообщение для рассылки (поддерживается форматирование Telegram):",
        reply_markup=back_to_message_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@message_admin_router.message(BroadcastState.entering_message)
async def receive_message_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    text = message.text or message.caption

    if text and len(text) > 4096:
        sent = await message.answer(
            "❗️Сообщение слишком длинное. Попробуйте ещё раз:",
            reply_markup=back_to_message_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
        return

    msg_data = {
        "text": text,
        "entities": message.entities or message.caption_entities,
        "photo": message.photo[-1].file_id if message.photo else None,
    }
    await state.update_data(**msg_data)
    await state.set_state(BroadcastState.choosing_time)
    sent = await message.answer(
        "Когда отправить сообщение? Введите время в формате ЧЧ:ММ или выберите:",
        reply_markup=time_choice_keyboard(),
    )
    await state.update_data(last_bot_message_id=sent.message_id)


@message_admin_router.callback_query(F.data == "send_now")
async def send_now(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sent = await callback.message.edit_text(
        "📤 Рассылка запущена...\n0%", reply_markup=admin_back_keyboard()
    )

    # Передаём данные для прогресса
    data["progress_message_chat_id"] = callback.message.chat.id
    data["progress_message_id"] = sent.message_id

    await send_broadcast(callback.bot, data)
    await state.clear()


@message_admin_router.message(BroadcastState.choosing_time)
async def schedule_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get("last_bot_message_id")
    if last_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, last_msg_id)
        except Exception:
            pass
    try:
        t = datetime.strptime(message.text.strip(), "%H:%M").time()
        data = await state.get_data()
        now = datetime.now(kyiv_tz)
        send_at = kyiv_tz.localize(datetime.combine(now.date(), t))
        if send_at < now:
            send_at = kyiv_tz.localize(
                datetime.combine(now.date(), t) + timedelta(days=1)
            )
        delay = (send_at - now).total_seconds()

        # Отправляем сообщение с прогрессом
        progress_msg = await message.answer(
            f"📤 Рассылка будет отправлена в {t.strftime('%H:%M')}\nОжидание запуска...",
            reply_markup=admin_back_keyboard(),
        )

        # Обновляем данные, чтобы send_broadcast получил chat_id и message_id
        data["progress_message_chat_id"] = progress_msg.chat.id
        data["progress_message_id"] = progress_msg.message_id

        asyncio.create_task(delayed_broadcast(message.bot, delay, data))
        await state.clear()
    except ValueError:
        sent = await message.answer(
            "Неверный формат времени. Введите в формате ЧЧ:ММ",
            reply_markup=back_to_message_keyboard(),
        )
        await state.update_data(last_bot_message_id=sent.message_id)
