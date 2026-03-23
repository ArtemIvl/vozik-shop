from telethon import TelegramClient
from telethon import functions, types
from db.models.user import User
from datetime import datetime, timezone

TEDDY_GIFT_ID = 5170233102089322756
API_ID = 23493250  # вставь свой API ID
API_HASH = "5ce6c82cba61c6059a17b7ee37a2d9d0"  # вставь свой API Hash
SESSION = "userbot_session"  # имя файла сессии
REFERRAL_CUTOFF_DATETIME = datetime(2025, 8, 6, 21, 0, 0, tzinfo=timezone.utc)

GIFT_MESSAGES = {
    "EN": "Thank you for using Vozik Shop!",
    "UA": "Дякуємо, що користуєтеся Vozik Shop!",
    "RU": "Спасибо, что пользуетесь Vozik Shop!",
    "default": "Спасибо, что пользуетесь Vozik Shop!",
}


async def list_star_gifts():
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        result = await client(
            functions.payments.GetSavedStarGiftsRequest(
                peer=await client.get_input_entity("username"),
                offset="some string here",
                limit=100,
            )
        )
        print(result)


async def handle_referral_gift_if_needed(referrer: User) -> None:
    active = referrer.active_referral_count
    # подарок на 3, 8, 13, 18 и т.д.
    if active >= 3 and (active == 3 or (active - 3) % 5 == 0):
        if referrer.username:
            await send_teddy_gift(referrer.username, referrer.language)


async def send_teddy_gift(recipient_username: str, lang_code: str = "default"):
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        # Получаем InputPeer для получателя
        recipient = await client.get_input_entity(recipient_username)

        raw_text = GIFT_MESSAGES.get(lang_code, GIFT_MESSAGES["default"])
        text_with_entities = types.TextWithEntities(text=raw_text, entities=[])

        # Создаем инвойс на подарок
        invoice = types.InputInvoiceStarGift(
            peer=recipient,
            gift_id=TEDDY_GIFT_ID,
            hide_name=False,
            message=text_with_entities,
        )

        # Получаем платежную форму
        payment_form = await client(
            functions.payments.GetPaymentFormRequest(invoice=invoice)
        )

        # Оплачиваем и отправляем подарок
        result = await client(
            functions.payments.SendStarsFormRequest(
                form_id=payment_form.form_id, invoice=invoice
            )
        )
        print("Подарок отправлен:", result)
