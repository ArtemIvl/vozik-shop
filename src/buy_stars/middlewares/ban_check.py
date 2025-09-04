import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, F, Router, types
from aiogram.types import CallbackQuery, Message
from db.session import SessionLocal
from requests.user_requests import get_user_by_telegram_id

router = Router()


def register_ban_payment_handler(dp) -> None:
    dp.include_router(router)


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        telegram_id = event.from_user.id

        async with SessionLocal() as session:
            user = await get_user_by_telegram_id(session, telegram_id)

            if user and user.is_banned:

                text = "❗Вы были заблокированы. Чтобы вернуть доступ, оплатите 99⭐️ через Telegram Stars."
                chat_id = (
                    event.message.chat.id
                    if isinstance(event, types.CallbackQuery)
                    else event.chat.id
                )
                await event.bot.send_message(chat_id, text)
                return
            
        return await handler(event, data)
