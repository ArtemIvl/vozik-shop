from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TON_WALLET_ADDRESS
from decimal import Decimal
from services.localization import t


def stars_username_keyboard(lang: str, username: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=f"{t(lang, 'keyboards.buy_stars.for_myself')} (@{username})",
                callback_data="stars_for_self",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{t(lang, 'keyboards.buy_stars.for_other')}",
                callback_data="stars_for_other",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.back"), callback_data="back"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def payment_method_keyboard(lang: str) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.for_ton"), callback_data="buy_for_ton"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.for_usd"),
                callback_data="buy_for_usdt",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.back"), callback_data="back"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def open_tonkeeper_keyboard(
    lang: str, price: Decimal, memo: str
) -> InlineKeyboardMarkup:
    ton_amount = int(price * Decimal("1e9"))  # TON → nanotons
    url = f"ton://transfer/{TON_WALLET_ADDRESS}?amount={ton_amount}&text={memo}"

    inline_keyboard = [
        [InlineKeyboardButton(text=t(lang, "keyboards.buy_stars.tonkeeper"), url=url)],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.confirm_payment"),
                callback_data="confirm_payment",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "keyboards.buy_stars.back"), callback_data="back"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def heleket_invoice_keyboard(lang: str, payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "keyboards.buy_stars.heleket"), url=payment_url
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "keyboards.buy_stars.back"), callback_data="back"
                )
            ],
        ]
    )
