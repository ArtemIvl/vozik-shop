import random
from decimal import Decimal, ROUND_UP
import httpx

TONAPI_RATES_URL = "https://tonapi.io/v2/rates?tokens=ton&currencies=usd"

USD_PRICE_PER_STAR = Decimal("0.015")
MARKUP = Decimal("1.11")
PREMIUM_PRICES_USD = {
    3: Decimal("12"),
    6: Decimal("16"),
    12: Decimal("29"),
}

def generate_memo() -> str:
    return str(random.randint(10000000, 99999999))


async def get_ton_price_usd() -> Decimal:
    async with httpx.AsyncClient() as client:
        response = await client.get(TONAPI_RATES_URL)
        response.raise_for_status()
        data = response.json()

    ton_usd_price = data["rates"]["TON"]["prices"]["USD"]
    return Decimal(str(ton_usd_price))


async def calculate_star_price_in_ton(star_amount: int) -> Decimal:
    ton_usd_price = await get_ton_price_usd()

    total_usd = USD_PRICE_PER_STAR * star_amount
    total_ton = (total_usd / ton_usd_price) * MARKUP

    return total_ton.quantize(Decimal("0.001"), rounding=ROUND_UP)


async def calculate_premium_price_in_ton(months: int) -> Decimal:
    if months not in PREMIUM_PRICES_USD:
        raise ValueError("Invalid subscription duration")

    base_usd = PREMIUM_PRICES_USD[months]
    final_usd = base_usd * Decimal("1.05")

    ton_usd_price = await get_ton_price_usd()
    price_in_ton = (final_usd / ton_usd_price).quantize(Decimal("0.001"), rounding=ROUND_UP)

    return price_in_ton
