from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="Управление пользователями", callback_data="manage_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="Управление выводами", callback_data="manage_withdrawals"
            )
        ],
        [
            InlineKeyboardButton(
                text="Статистика", callback_data="bot_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отправить сообщение", callback_data="send_message"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [[InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
