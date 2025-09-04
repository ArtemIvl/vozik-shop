from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from db.session import SessionLocal
from db.models.user import Language
from services.localization import t, get_lang

from requests.user_requests import get_user_by_telegram_id, add_user, increment_referral_count
from keyboards.menu_keyboard import menu_button_keyboard, menu_keyboard
from keyboards.language_keyboard import start_language_selection_keyboard
from keyboards.settings_keyboard import settings_keyboard

router = Router()

def register_start_handlers(dp) -> None:
    dp.include_router(router)

class Register(StatesGroup):
    choose_language = State()

@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    parts = message.text.split()
    telegram_id = message.from_user.id
    username = message.from_user.username
    referred_by_id = None

    if len(parts) > 1:
        try:
            referred_by_id = int(parts[1])
        except ValueError:
            referred_by_id = None


    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user:
            lang = await get_lang(message.from_user.id)
            await message.answer(text=t(lang, 'start.welcome_back'), reply_markup=menu_button_keyboard(lang))
            return
        else:
            await state.set_data({
                "telegram_id": telegram_id,
                "username": username,
                "referred_by_id": referred_by_id,
            })

            await state.set_state(Register.choose_language)

            await message.answer(
                "🌍 Please choose your language:\n\n🌍 Будь ласка, оберіть мову:\n\n🌍 Пожалуйста, выберите язык:",
                reply_markup=start_language_selection_keyboard()
            )

@router.callback_query(F.data.startswith("lang_"), Register.choose_language)
async def language_chosen(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language_code = callback.data.split("_")[1]
    language = Language(language_code.upper())

    async with SessionLocal() as session:
        referrer = None
        if data.get("referred_by_id"):
            referrer = await get_user_by_telegram_id(session, data["referred_by_id"])

        existing_user = await get_user_by_telegram_id(session, data["telegram_id"])
        if not existing_user:
            await add_user(
                session,
                telegram_id=data["telegram_id"],
                username=data["username"],
                referred_by=referrer.id if referrer else None,
                language=language,
            )

            if referrer:
                await increment_referral_count(session, referrer.id)

    text = (
        f"{t(language.value.lower(), 'start.welcome')}\n\n"
        f"{t(language.value.lower(), 'start.info')}"
    )

    await callback.message.answer(text, reply_markup=menu_button_keyboard(language.value.lower()))
    await state.clear()

@router.message(F.text.in_({"/menu", "⭐ Menu", "⭐ Меню"}))
async def menu_callback(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        lang = await get_lang(message.from_user.id)
    if user:
        await message.answer(
            t(lang, 'menu.description'),
            parse_mode="HTML",
            reply_markup=menu_keyboard(lang),
        )
    else:
        await message.answer("Please, register by clicking /start.\n\nБудь ласка, зареєструйтесь, натиснувши /start.\n\nПожалуйста, зарегистрируйтесь нажав /start.")

@router.callback_query(F.data == "back")
async def menu_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, 'menu.description'),
        parse_mode="HTML",
        reply_markup=menu_keyboard(lang),
    )


@router.callback_query(F.data == "settings")
async def settings_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text(
            t(lang, 'menu.settings'),
            parse_mode="HTML",
            reply_markup=settings_keyboard(lang),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

@router.callback_query(F.data == "back_settings")
async def settings_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text(
            t(lang, 'menu.settings'),
            parse_mode="HTML",
            reply_markup=settings_keyboard(lang),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

