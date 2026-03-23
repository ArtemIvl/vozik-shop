from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def time_choice_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="Сейчас", callback_data="send_now")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="send_message")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def back_to_message_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
