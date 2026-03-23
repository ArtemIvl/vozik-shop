from aiogram import types, Router, F
from db.session import SessionLocal
import re

from requests.user_requests import get_user_by_telegram_id
from keyboards.withdraw_keyboard import withdraw_keyboard
from aiogram.fsm.context import FSMContext
from services.localization import t, get_lang
from services.profile_stats import format_decimal, get_profile_stats

router = Router()


def register_profile_handlers(dp) -> None:
    dp.include_router(router)


def _clean_profile_label(value: str) -> str:
    if value.startswith("<b>"):
        return re.sub(r"^<b>\W*", "<b>", value, count=1)
    return re.sub(r"^\W*", "", value, count=1)


@router.callback_query(F.data == "profile")
async def handle_profile(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    lang = await get_lang(callback.from_user.id)

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        if not user:
            await callback.answer(t(lang, "profile.not_found"), show_alert=True)
            return

        referral_link = f"https://t.me/VozikStarsBot?start={telegram_id}"
        stats = await get_profile_stats(session, user)

        ref_balance = user.balance or 0

    ref_balance_str = format_decimal(ref_balance, places=2)
    saved_wallet = user.default_ton_wallet or "—"

    text = (
        f"<b>{t(lang, 'keyboards.menu.profile')}</b>\n\n"
        f"{_clean_profile_label(t(lang, 'profile.balance'))} {ref_balance_str} USDT\n\n"
        f"<blockquote>{_clean_profile_label(t(lang, 'profile.saved_wallet'))} <code>{saved_wallet}</code></blockquote>\n\n"
        f"<b>📊 {t(lang, 'profile.referral_stats')}</b>\n"
        f"<blockquote>{_clean_profile_label(t(lang, 'profile.referrals'))} {user.referral_count or 0}\n"
        f"{_clean_profile_label(t(lang, 'profile.active_referrals'))} {user.active_referral_count or 0}\n"
        f"{_clean_profile_label(t(lang, 'profile.referral_earned'))} {stats['referralEarnedUsdt']} USDT\n"
        f"{t(lang, 'profile.commission_short')}: <b>{format_decimal(user.referral_commission * 100, places=2)}%</b></blockquote>\n\n"
        f"<b>🧾 {t(lang, 'profile.activity')}</b>\n"
        f"<blockquote>{_clean_profile_label(t(lang, 'profile.total_orders'))} {stats['totalOrdersCount']}\n"
        f"{_clean_profile_label(t(lang, 'profile.purchased_stars'))} {stats['purchasedStarsTotal']}\n"
        f"{_clean_profile_label(t(lang, 'profile.exchanged_stars'))} {stats['exchangedStarsTotal']}\n"
        f"{_clean_profile_label(t(lang, 'profile.received_ton'))} {stats['receivedUsdtTotal']} USDT</blockquote>\n\n"
        f"<b>🔗 {t(lang, 'profile.referral_link')}</b>\n"
        f"<blockquote>{referral_link}</blockquote>\n\n"
        f"{t(lang, 'profile.info')}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=withdraw_keyboard(lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()
