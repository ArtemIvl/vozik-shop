from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.localization import t


def sell_stars_quote_keyboard(lang: str, order_id: int, stars_amount: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{t(lang, 'keyboards.sell_stars.pay')} {stars_amount} ⭐️",
                callback_data=f"sell_stars_pay_{order_id}",
            )
        ],
        [
            InlineKeyboardButton(text=t(lang, "keyboards.sell_stars.back"), callback_data="back"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
