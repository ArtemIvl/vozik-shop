import asyncio
from db.session import SessionLocal
from services.fragment import buy_stars, buy_premium
from requests.order_requests import (
    get_pending_orders, mark_order_paid, mark_order_cancelled, mark_order_failed, mark_order_processing
)
from requests.user_requests import add_referral_bonus, check_and_increment_active_referral, get_user_by_id
from config import TON_WALLET_ADDRESS
from db.models.order import Order, OrderType, PaymentType
from aiogram import Bot
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import httpx
from services.localization import t, get_lang
from services.gift import handle_referral_gift_if_needed


async def check_payments(bot: Bot):
    async with SessionLocal() as session:
        pending_orders = await get_pending_orders(session)

        now = datetime.now(timezone.utc)
        for order in pending_orders:
            if order.created_at and now - order.created_at > timedelta(minutes=30):
                await mark_order_cancelled(session, order.id)

        pending_orders = await get_pending_orders(session)

        ton_orders = [o for o in pending_orders if o.payment_type == PaymentType.TON]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://tonapi.io/v2/blockchain/accounts/{TON_WALLET_ADDRESS}/transactions"
            )
            response.raise_for_status()
            tx_data = response.json().get("transactions", [])
    except Exception as e:
        print(f"[check_payments] Ошибка при получении транзакций: {e}")
        return
    
    for order in ton_orders:
        await process_order(order, tx_data, bot)


async def process_order(order: Order, tx_data: list, bot: Bot):
    try:
        async with SessionLocal() as session:
            tx = find_matching_transaction(tx_data, order.memo, order.price_ton)
            if not tx:
                return
            
            await mark_order_processing(session, order.id)
            
            lang = await get_lang(order.user.telegram_id)

            # Покупка в зависимости от типа
            if order.order_type == OrderType.STARS:
                try:
                    success = await try_buy_stars(order.to_username, order.stars_amount)
                except Exception as e:
                    print(f"[process_order] Ошибка при try_buy_stars: {e}")
                    return  # не маркируем как failed, повторим позже
            elif order.order_type == OrderType.PREMIUM:
                try:
                    success = await try_buy_premium(order.to_username, order.premium_months)
                except Exception as e:
                    print(f"[process_order] Ошибка при try_buy_premium: {e}")
                    return
            else:
                await bot.send_message(order.user.telegram_id, t(lang, 'payment.unknown_order'))
                return

            if not success:
                await mark_order_failed(session, order.id)
                print(f"[process_order] Покупка не удалась, но транзакция найдена. Order #{order.id}")
                await bot.send_message(order.user.telegram_id, t(lang, "payment.order_failed"))
                return  # mark_failed — потому что TON уже пришёл, но Fragment не дал ответ, можно повторить по кнопке

            # ✅ Покупка удалась
            try:
                await mark_order_paid(session, order.id)
            except Exception as e:
                print(f"[process_order] Не удалось пометить заказ как оплачен: {e}")
                return  # повторим позже, звёзды уже выданы, но база не обновилась
            
            gift_bonus = await check_and_increment_active_referral(session, order.user.id)

            # 💸 Реферальный бонус
            bonuses = await add_referral_bonus(session, order.user, order.price_ton, order.order_type)

            # ✉️ Уведомление пользователю
            if order.order_type == OrderType.PREMIUM:
                result_text = f"{t(lang, 'payment.premium_confirm_1')} @{order.to_username} {t(lang, 'payment.premium_confirm_2')}"
            else:
                result_text = f"{t(lang, 'payment.stars_confirm_1')} @{order.to_username} {t(lang, 'payment.stars_confirm_2')}"

            await bot.send_message(order.user.telegram_id, result_text)

            if gift_bonus:
                referrer = await get_user_by_id(session, order.user.referred_by)
                await handle_referral_gift_if_needed(referrer)

            # ✉️ Реферреру
            if bonuses:
                for referrer, bonus in bonuses:
                    lang = await get_lang(referrer.telegram_id)
                    await bot.send_message(
                        referrer.telegram_id,
                        f"{t(lang, 'payment.referral_confirm_1')} {bonus:.4f} {t(lang, 'payment.referral_confirm_2')}"
                    )
    except Exception as e:
        print(f"[process_order] Ошибка в заказе #{order.id}: {e}")
        try:
            lang = await get_lang(order.user.telegram_id)
            await bot.send_message(order.user.telegram_id, t(lang, 'payment.error_processing'))
        except Exception:
            pass

async def try_buy_stars(username, amount) -> bool:
    try:
        return await buy_stars(username, amount)
    except httpx.ReadTimeout:
        print(f"❗ Timeout while buying stars for @{username}")
        return False
    except Exception as e:
        print(f"❗ Unexpected error in try_buy_stars: {e}")
        return False


async def try_buy_premium(username, months) -> bool:
    try:
        return await buy_premium(username, months)
    except httpx.ReadTimeout:
        print(f"❗ Timeout while buying premium for @{username}")
        return False
    except Exception as e:
        print(f"❗ Unexpected error in try_buy_premium: {e}")
        return False


def find_matching_transaction(tx_data: list, memo: str, expected_amount: Decimal) -> dict | None:
    for tx in tx_data:
        extracted = extract_memo_from_tx(tx)
        if not extracted or extracted.strip() != memo:
            continue

        try:
            actual = Decimal(tx["in_msg"].get("value", "0")) / Decimal("1e9")
            if actual >= expected_amount:
                return tx
        except Exception:
            continue
    return None


def extract_memo_from_tx(tx: dict) -> str | None:
    in_msg = tx.get("in_msg", {})
    decoded = in_msg.get("decoded_body", {}).get("text")
    if decoded:
        return decoded

    payload = in_msg.get("payload")
    if payload:
        try:
            return bytes.fromhex(payload).decode("utf-8")
        except Exception:
            pass

    return in_msg.get("comment")