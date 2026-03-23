from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.models.withdrawal import Withdrawal, WithdrawalStatus
from sqlalchemy.ext.asyncio import AsyncSession


def withdraw_info_keyboard(withdrawal_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить вывод",
                callback_data=f"confirm_withdrawal_{withdrawal_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отклонить вывод",
                callback_data=f"reject_withdrawal_{withdrawal_id}",
            ),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="manage_withdrawals"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)



async def pending_withdraw_keyboard(
    session: AsyncSession, withdrawals: list[Withdrawal], page: int, per_page: int = 10
) -> InlineKeyboardMarkup:
    start = (page - 1) * per_page
    end = start + per_page
    total = len(withdrawals)
    pages = (total + per_page - 1) // per_page

    inline_keyboard = []

    for withdrawal in withdrawals[start:end]:
        if withdrawal.status == WithdrawalStatus.PENDING:
            inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"Вывод на сумму {withdrawal.ton_amount} USDT",
                        callback_data=f"withdraw_info_{withdrawal.id}",
                    )
                ]
            )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"withdraw_page_{page - 1}")
        )
    if page < pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"withdraw_page_{page + 1}")
        )
    if nav_buttons:
        inline_keyboard.append(nav_buttons)

    inline_keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin")]
    )

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def confirm_withdraw_keyboard(withdrawal_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="✅ Да, подтвердить", callback_data=f"confirm_final_{withdrawal_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"withdraw_info_{withdrawal_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def reject_withdraw_keyboard(withdrawal_id: int) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(text="❌ Да, отклонить", callback_data=f"reject_final_{withdrawal_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"withdraw_info_{withdrawal_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
