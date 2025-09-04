from aiogram import types, Router, F
from db.session import SessionLocal

from requests.user_requests import get_user_by_telegram_id
from keyboards.withdraw_keyboard import withdraw_keyboard
from aiogram.fsm.context import FSMContext
from services.localization import t, get_lang

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

        ref_balance = user.referral_balance or 0
        ref_total_earned = user.referral_total_earned or 0

    ref_balance_str = f"{ref_balance:.4f}" if ref_balance > 0 else "0.0"
    ref_total_str = f"{ref_total_earned:.4f}" if ref_total_earned > 0 else "0.0"

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
        f"{t(lang, 'profile.info')}"
    )

    await callback.message.edit_text(text, reply_markup=withdraw_keyboard(lang), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()