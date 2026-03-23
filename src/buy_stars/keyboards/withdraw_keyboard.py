from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.localization import t

def withdraw_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.main'), callback_data="withdraw_referral"),
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.save_wallet'), callback_data="save_wallet")
        ],
        [
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


def saved_wallet_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.use_saved'), callback_data="withdraw_use_saved_wallet"),
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.change'), callback_data="withdraw_change_wallet"),
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.back'), callback_data="profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
