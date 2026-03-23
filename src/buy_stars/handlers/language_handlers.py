from aiogram import Router, F
from aiogram.types import CallbackQuery
from db.session import SessionLocal
from requests.user_requests import set_user_language
from keyboards.language_keyboard import language_selection_keyboard
from keyboards.withdraw_keyboard import back_to_profile_keyboard
from services.localization import t, get_lang

router = Router()

def register_language_handlers(dp) -> None:
    dp.include_router(router)


@router.callback_query(F.data == "language")
async def handle_language(callback: CallbackQuery):
    lang = await get_lang(callback.from_user.id)
    await callback.message.edit_text(t(lang, 'language.choose'), reply_markup=language_selection_keyboard(lang))

@router.callback_query(F.data.startswith("lang_"))
async def set_language_callback(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    async with SessionLocal() as session:
        await set_user_language(session, callback.from_user.id, lang_code.upper())
        lang = await get_lang(callback.from_user.id)
    await callback.message.edit_text(t(lang, 'language.changed'), reply_markup=back_to_profile_keyboard(lang))
