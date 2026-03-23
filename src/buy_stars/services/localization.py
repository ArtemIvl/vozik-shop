import json
import os
from requests.user_requests import get_user_by_telegram_id
from db.session import SessionLocal

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # путь до src/buy_stars
LOCALES_DIR = os.path.join(BASE_DIR, "locales")

with open(os.path.join(LOCALES_DIR, "en.json"), "r", encoding="utf-8") as f:
    EN = json.load(f)
with open(os.path.join(LOCALES_DIR, "ru.json"), "r", encoding="utf-8") as f:
    RU = json.load(f)
with open(os.path.join(LOCALES_DIR, "ua.json"), "r", encoding="utf-8") as f:
    UA = json.load(f)

LANGUAGES = {"en": EN, "ru": RU, "ua": UA}


def t(lang: str, key_path: str) -> str:
    keys = key_path.split(".")
    data = LANGUAGES.get(lang, EN)
    for key in keys:
        data = data.get(key, {})
    return data if isinstance(data, str) else ""


async def get_lang(telegram_id: int) -> str:
    async with SessionLocal() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        return user.language.value.lower() if user else "en"
