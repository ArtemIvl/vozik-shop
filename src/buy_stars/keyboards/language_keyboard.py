from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.localization import t

def start_language_selection_keyboard() -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def language_selection_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton(text=t(lang, 'keyboards.withdraw.back'), callback_data="profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)