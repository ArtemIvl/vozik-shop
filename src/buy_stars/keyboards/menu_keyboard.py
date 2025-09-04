from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from services.localization import t

def menu_button_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=t(lang, 'keyboards.menu.main'))]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

def menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.buy_stars'), callback_data="buy_stars"),
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.buy_tg_premium'), callback_data="buy_tg_premium")
        ],
        # [
        #     InlineKeyboardButton(text=t(lang, 'keyboards.menu.buy_tg_premium'), callback_data="buy_tg_premium")
        # ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.gift_promo'), callback_data="gift_promo")
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.profile'), callback_data="profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.back'), callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)