from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.localization import t


def premium_username_keyboard(lang: str, username: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{t(lang, 'keyboards.buy_tg_premium.for_myself')} (@{username})",
                callback_data="premium_for_self",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{t(lang, 'keyboards.buy_tg_premium.for_other')}",
                callback_data="premium_for_other",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_tg_premium.back"), callback_data="back"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def premium_duration_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_tg_premium.3_months"),
                callback_data="premium_months_3",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_tg_premium.6_months"),
                callback_data="premium_months_6",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_tg_premium.12_months"),
                callback_data="premium_months_12",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_tg_premium.back"), callback_data="back"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
