from fastapi import APIRouter, Request, HTTPException
from config import BOT_TOKEN, HELEKET_API_KEY
from aiogram import Bot
from db.models.order import OrderStatus, OrderType
from requests.order_requests import get_order_by_id, mark_order_paid, mark_order_failed
from requests.user_requests import (
    add_referral_bonus_usd,
    check_and_increment_active_referral,
    get_user_by_id,
)
from services.fragment import buy_premium, buy_stars
from db.session import SessionLocal
import json
import hashlib
import base64
from services.localization import t, get_lang
from services.gift import handle_referral_gift_if_needed
from services.admin_notifications import notify_admins_order_failed

bot = Bot(token=BOT_TOKEN)
router = APIRouter()


def verify_signature(data: dict, received_sign: str) -> bool:
    data_copy = dict(data)
    data_copy.pop("sign", None)  # важно удалить перед хешем

    raw = json.dumps(data_copy, ensure_ascii=False, separators=(",", ":"))
    base64_encoded = base64.b64encode(raw.encode()).decode()
    generated_sign = hashlib.md5(
        (base64_encoded + HELEKET_API_KEY).encode()
    ).hexdigest()

    return generated_sign == received_sign


@router.post("/heleket/webhook")
async def heleket_webhook(request: Request):
    print("✅ Webhook получен от Heleket!")
    raw_body = await request.body()
    print(f"📦 Raw body: {raw_body.decode()}")
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    sign = data.get("sign")
    if not sign or not verify_signature(data, sign):
        print("🚫 Подпись недействительна!")
        raise HTTPException(status_code=403, detail="Invalid signature")

    if data.get("status") not in ["paid", "paid_over"]:
        return {"ok": True, "message": "Not a completed payment"}

    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="No order_id")

    order_id = int(order_id)

    async with SessionLocal() as session:
        order = await get_order_by_id(session, order_id)
        if not order or order.status == OrderStatus.PAID:
            return {"ok": True, "message": "Order not found or already paid"}

        try:
            lang = await get_lang(order.user.telegram_id)
            if order.order_type == OrderType.STARS:
                try:
                    success = await buy_stars(order.to_username, order.stars_amount)
                except Exception as e:
                    print(f"[Webhook] Ошибка в try_buy_stars: {e}")
                    success = False

            elif order.order_type == OrderType.PREMIUM:
                try:
                    success = await buy_premium(order.to_username, order.premium_months)
                except Exception as e:
                    print(f"[Webhook] Ошибка в try_buy_premium: {e}")
                    success = False

            else:
                await bot.send_message(
                    order.user.telegram_id, t(lang, "payment.unknown_order")
                )
                return {"ok": False}

            if not success:
                await mark_order_failed(session, order.id)
                print(
                    f"[process_order] Покупка не удалась, но транзакция найдена. Order #{order.id}"
                )
                await bot.send_message(
                    order.user.telegram_id, t(lang, "payment.order_failed")
                )
                await notify_admins_order_failed(
                    bot, session, order, source="Heleket webhook"
                )
                return  # mark_failed — потому что TON уже пришёл, но Fragment не дал ответ, можно повторить по кнопке

            # Помечаем как оплаченный
            try:
                await mark_order_paid(session, order.id)
            except Exception as e:
                print(f"[Webhook] Не удалось пометить как оплачено: {e}")
                return {"ok": True, "message": "Retry later"}

            gift_bonus = await check_and_increment_active_referral(
                session, order.user.id
            )

            # Рефералка
            bonuses = await add_referral_bonus_usd(
                session, order.user, order.price_usdt, order.order_type
            )

            # Сообщение пользователю
            if order.order_type == OrderType.PREMIUM:
                msg = f"{t(lang, 'payment.premium_confirm_1')} @{order.to_username} {t(lang, 'payment.premium_confirm_2')}"
            else:
                msg = f"{t(lang, 'payment.stars_confirm_1')} @{order.to_username} {t(lang, 'payment.stars_confirm_2')}"
            await bot.send_message(order.user.telegram_id, msg)

            if gift_bonus:
                referrer = await get_user_by_id(session, order.user.referred_by)
                await handle_referral_gift_if_needed(referrer)

            if bonuses:
                for referrer, bonus in bonuses:
                    lang = await get_lang(referrer.telegram_id)
                    await bot.send_message(
                        referrer.telegram_id,
                        f"{t(lang, 'payment.referral_confirm_1')} {bonus:.2f} {t(lang, 'payment.referral_confirm_2')}",
                    )
        except Exception as e:
            print(f"[Webhook] Общая ошибка: {e}")
            try:
                lang = await get_lang(order.user.telegram_id)
                await bot.send_message(
                    order.user.telegram_id, t(lang, "payment.error_processing")
                )
            except Exception:
                pass

    return {"ok": True}
