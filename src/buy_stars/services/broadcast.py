import asyncio
from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramNotFound,
)
from db.session import SessionLocal
from requests.user_requests import get_all_users


async def send_broadcast(bot: Bot, data: dict) -> None:
    async with SessionLocal() as session:
        users = await get_all_users(session)
        total = len(users)
        success = 0
        failed = 0
        tasks = []

        progress_msg_chat_id = data.get("progress_message_chat_id")
        progress_msg_id = data.get("progress_message_id")

        sem = asyncio.Semaphore(20)

        async def send_to_user(user, idx):
            nonlocal success, failed
            try:
                async with sem:
                    if data.get("photo"):
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=data["photo"],
                            caption=data.get("text"),
                            caption_entities=data.get("entities"),
                        )
                    else:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=data["text"],
                            entities=data.get("entities"),
                        )
                    success += 1
            except (TelegramForbiddenError, TelegramNotFound):
                failed += 1
            except (TelegramBadRequest, TelegramAPIError, TelegramNetworkError):
                failed += 1
            except Exception:
                failed += 1

            # Статус-бар каждый 10 пользователей
            if (idx + 1) % 10 == 0 and progress_msg_chat_id:
                try:
                    percent = int((idx + 1) / total * 100)
                    await bot.edit_message_text(
                        f"📤 Рассылка сообщений...\n{percent}% ({idx + 1}/{total})",
                        chat_id=progress_msg_chat_id,
                        message_id=progress_msg_id,
                    )
                except Exception:
                    pass

        for idx, user in enumerate(users):
            tasks.append(send_to_user(user, idx))

        await asyncio.gather(*tasks)

        # Финальный отчёт
        if progress_msg_chat_id:
            try:
                await bot.edit_message_text(
                    f"✅ Рассылка завершена\n\n"
                    f"Успешно: {success}/{total}\n"
                    f"Неудачно: {failed}/{total}\n",
                    chat_id=progress_msg_chat_id,
                    message_id=progress_msg_id,
                )
            except Exception:
                pass


async def delayed_broadcast(bot, delay: float, data: dict) -> None:
    await asyncio.sleep(delay)
    await send_broadcast(bot, data)
