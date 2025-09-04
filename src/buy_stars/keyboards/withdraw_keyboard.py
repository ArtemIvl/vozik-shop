from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.localization import t

def withdraw_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.main'), callback_data="withdraw_referral"),
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.language'), callback_data="language")
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.support'), url="https://t.me/VozikShop_support"),
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.menu.back'), callback_data="back")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def back_to_profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.back'), callback_data="profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)