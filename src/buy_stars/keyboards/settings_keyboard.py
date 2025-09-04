from services.localization import t
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.support'), url="https://t.me/VozikShop_support"),
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.language'), callback_data="language")
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.back'), callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.back_settings'), callback_data="back_settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)