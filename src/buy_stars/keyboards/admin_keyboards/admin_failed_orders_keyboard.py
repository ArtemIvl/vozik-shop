from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.order import Order, OrderType


async def failed_orders_keyboard(
    orders: list[Order], page: int, per_page: int = 10
) -> InlineKeyboardMarkup:
    start = (page - 1) * per_page
    end = start + per_page
    total = len(orders)
    pages = (total + per_page - 1) // per_page

    inline_keyboard = []

    for order in orders[start:end]:
        item_type = "⭐" if order.order_type == OrderType.STARS else "💎"
        item_amount = order.stars_amount or order.premium_months
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{item_type} #{order.id} | @{order.to_username} | {item_amount}",
                    callback_data=f"failed_order_info_{order.id}",
                )
            ]
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"failed_orders_page_{page - 1}")
        )
    if page < pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"failed_orders_page_{page + 1}")
        )
    if nav_buttons:
        inline_keyboard.append(nav_buttons)

    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def failed_order_info_keyboard(order_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🔁 Повторить отправку", callback_data=f"retry_failed_order_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К списку", callback_data="manage_failed_orders"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
