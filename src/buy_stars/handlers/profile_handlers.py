from aiogram import types, Router, F
from db.session import SessionLocal

from requests.user_requests import get_user_by_telegram_id
from keyboards.withdraw_keyboard import withdraw_keyboard
from aiogram.fsm.context import FSMContext
from services.localization import t, get_lang
from services.profile_stats import format_decimal, get_profile_stats

router = Router()

def register_profile_handlers(dp) -> None:
    dp.include_router(router)

@router.callback_query(F.data == "profile")
async def handle_profile(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    telegram_id = callback.from_user.id
    lang = await get_lang(callback.from_user.id)

    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)

        if not user:
            await callback.answer(t(lang, 'profile.not_found'), show_alert=True)
            return

        referral_link = f"https://t.me/VozikStarsBot?start={telegram_id}"
        stats = await get_profile_stats(session, user)

        ref_balance = user.referral_balance or 0
        ref_total_earned = user.referral_total_earned or 0

    ref_balance_str = format_decimal(ref_balance, places=4)
    ref_total_str = format_decimal(ref_total_earned, places=4)
    saved_wallet = user.default_ton_wallet or "—"

    text = (
        f"{t(lang, 'profile.description')} "
        f"<b>{user.referral_commission * 100}</b>{t(lang, 'profile.commission')}\n\n"
        f"{t(lang, 'profile.referral_link')}\n"
        f"{referral_link}\n\n"
        f"{t(lang, 'profile.referral_stats')}\n"
        f"{t(lang, 'profile.referrals')} {user.referral_count or 0}\n"
        f"{t(lang, 'profile.active_referrals')} {user.active_referral_count or 0}\n"
        f"{t(lang, 'profile.balance')} {ref_balance_str} TON\n"
        f"{t(lang, 'profile.total_earned')} {ref_total_str} TON\n\n"
        f"{t(lang, 'profile.saved_wallet')} <code>{saved_wallet}</code>\n\n"
        f"{t(lang, 'profile.total_orders')} {stats['totalOrdersCount']}\n"
        f"{t(lang, 'profile.purchased_stars')} {stats['purchasedStarsTotal']}\n"
        f"{t(lang, 'profile.exchanged_stars')} {stats['exchangedStarsTotal']}\n"
        f"{t(lang, 'profile.received_ton')} {stats['receivedTonTotal']} TON\n"
        f"{t(lang, 'profile.referral_earned')} {stats['referralEarnedTon']} TON\n\n"
        f"{t(lang, 'profile.info')}"
    )

    await callback.message.edit_text(text, reply_markup=withdraw_keyboard(lang), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()
