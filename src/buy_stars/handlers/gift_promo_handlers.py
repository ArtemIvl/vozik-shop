from aiogram import types, Router, F
from aiogram.types import FSInputFile
from services.localization import t, get_lang
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path

PHOTO_PATH = Path(__file__).parent.parent / "images" / "gift-bear.jpeg"

router = Router()

def register_gift_promo_handlers(dp) -> None:
    dp.include_router(router)

@router.callback_query(F.data == "gift_promo")
async def send_gift_info(callback: types.CallbackQuery) -> None:
    builder = InlineKeyboardBuilder()
    lang = await get_lang(callback.from_user.id)
    builder.button(text=t(lang, 'keyboards.menu.back'), callback_data="delete_info_text")
    await callback.message.answer_photo(
        photo=FSInputFile(PHOTO_PATH),
        caption=t(lang, 'menu.gift_promo'),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "delete_info_text")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()