from aiogram import F, Router, types
from db.models.order import OrderType
from db.session import SessionLocal
from keyboards.admin_keyboards import failed_order_info_keyboard, failed_orders_keyboard
from requests.order_requests import (
    get_failed_orders,
    get_order_by_id,
    mark_failed_order_processing,
    mark_order_failed,
    mark_order_paid,
)
from requests.user_requests import (
    add_referral_bonus,
    add_referral_bonus_usd,
    check_and_increment_active_referral,
    get_user_by_id,
)
from services.fragment import buy_premium, buy_stars
from services.gift import handle_referral_gift_if_needed
from services.localization import get_lang, t

failed_orders_admin_router = Router()


@failed_orders_admin_router.callback_query(F.data == "manage_failed_orders")
async def manage_failed_orders_callback(callback: types.CallbackQuery) -> None:
    async with SessionLocal() as session:
        orders = await get_failed_orders(session)

    if not orders:
        await callback.message.edit_text(
            "Неудачных транзакций нет.",
            reply_markup=await failed_orders_keyboard([], page=1),
        )
        return

    await callback.message.edit_text(
        "Список неудачных транзакций:",
        reply_markup=await failed_orders_keyboard(orders, page=1),
    )


@failed_orders_admin_router.callback_query(F.data.startswith("failed_orders_page_"))
async def failed_orders_page_callback(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split("_")[-1])
    async with SessionLocal() as session:
        orders = await get_failed_orders(session)

    await callback.message.edit_text(
        "Список неудачных транзакций:",
        reply_markup=await failed_orders_keyboard(orders, page=page),
    )
    await callback.answer()


@failed_orders_admin_router.callback_query(F.data.startswith("failed_order_info_"))
async def failed_order_info_callback(callback: types.CallbackQuery) -> None:
    order_id = int(callback.data.split("_")[-1])

    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order_kind = "Stars" if order.order_type == OrderType.STARS else "Premium"
    amount = (
        order.stars_amount
        if order.order_type == OrderType.STARS
        else order.premium_months
    )
    price = order.price_ton if order.price_ton is not None else order.price_usdt
    created_at = (
        order.created_at.strftime("%d.%m.%Y %H:%M UTC") if order.created_at else "-"
    )

    text = (
        f"❗️Транзакция #{order.id}\n\n"
        f"👤 Пользователь: @{order.user.username} | {order.user.telegram_id}\n"
        f"🎯 Для: @{order.to_username}\n"
        f"📦 Тип: {order_kind}\n"
        f"🔢 Кол-во: {amount}\n"
        f"💳 Оплата: {order.payment_type.value}\n"
        f"💰 Сумма: {price}\n"
        f"🧾 Memo: <code>{order.memo}</code>\n"
        f"📅 Создан: {created_at}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=failed_order_info_keyboard(order.id),
    )


@failed_orders_admin_router.callback_query(F.data.startswith("retry_failed_order_"))
async def retry_failed_order_callback(callback: types.CallbackQuery) -> None:
    order_id = int(callback.data.split("_")[-1])

    async with SessionLocal() as session:
        locked = await mark_failed_order_processing(session, order_id)
        if not locked:
            await callback.answer(
                "Заказ уже обрабатывается или не в FAILED", show_alert=True
            )
            return

        order = await get_order_by_id(session, order_id)
        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        lang = await get_lang(order.user.telegram_id)

        if order.order_type == OrderType.STARS:
            success = await safe_buy_stars(order.to_username, order.stars_amount)
        else:
            success = await safe_buy_premium(order.to_username, order.premium_months)

        if not success:
            await mark_order_failed(session, order.id)
            await callback.bot.send_message(
                order.user.telegram_id, t(lang, "payment.order_failed")
            )
            await callback.answer(
                "Не удалось отправить, заказ снова в FAILED", show_alert=True
            )
            return

        await mark_order_paid(session, order.id)

        gift_bonus = await check_and_increment_active_referral(session, order.user.id)

        if order.payment_type.value == "USDT":
            bonuses = await add_referral_bonus_usd(
                session, order.user, order.price_usdt, order.order_type
            )
        else:
            bonuses = await add_referral_bonus(
                session, order.user, order.price_ton, order.order_type
            )

        if order.order_type == OrderType.PREMIUM:
            result_text = f"{t(lang, 'payment.premium_confirm_1')} @{order.to_username} {t(lang, 'payment.premium_confirm_2')}"
        else:
            result_text = f"{t(lang, 'payment.stars_confirm_1')} @{order.to_username} {t(lang, 'payment.stars_confirm_2')}"

        await callback.bot.send_message(order.user.telegram_id, result_text)

        if gift_bonus:
            referrer = await get_user_by_id(session, order.user.referred_by)
            await handle_referral_gift_if_needed(referrer)

        if bonuses:
            for referrer, bonus in bonuses:
                ref_lang = await get_lang(referrer.telegram_id)
                await callback.bot.send_message(
                    referrer.telegram_id,
                    f"{t(ref_lang, 'payment.referral_confirm_1')} {bonus:.2f} {t(ref_lang, 'payment.referral_confirm_2')}",
                )

    await callback.answer("Повторная отправка выполнена", show_alert=True)
    await manage_failed_orders_callback(callback)


async def safe_buy_stars(username: str, amount: int) -> bool:
    try:
        return await buy_stars(username, amount)
    except Exception:
        return False


async def safe_buy_premium(username: str, months: int) -> bool:
    try:
        return await buy_premium(username, months)
    except Exception:
        return False
