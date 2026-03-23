from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from db.models.order import Order, OrderType, PaymentType
from requests.user_requests import get_all_admins


async def notify_admins_order_failed(
    bot: Bot, session, order: Order, source: str
) -> None:
    admins = await get_all_admins(session)

    order_kind = "stars" if order.order_type == OrderType.STARS else "premium"
    payment_kind = "TON" if order.payment_type == PaymentType.TON else "USDT"
    amount = (
        order.stars_amount
        if order.order_type == OrderType.STARS
        else order.premium_months
    )

    text = (
        "❗️Неудачная транзакция Fragment\n"
        f"Order: #{order.id}\n"
        f"Тип: {order_kind}\n"
        f"Кол-во: {amount}\n"
        f"Для: @{order.to_username}\n"
        f"Оплата: {payment_kind}\n"
        f"Источник: {source}"
    )

    for admin in admins:
        try:
            await bot.send_message(admin.telegram_id, text)
        except TelegramForbiddenError:
            continue
        except Exception:
            continue
