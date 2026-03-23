import httpx
from decimal import Decimal
import hashlib
import base64
import json
from config import HELEKET_API_KEY, HELEKET_MERCHANT_ID, HELEKET_WEBHOOK_URL


async def create_heleket_invoice(amount_usd: Decimal, order_id: str) -> str | None:
    payload = {
        "project_id": HELEKET_MERCHANT_ID,
        "amount": str(amount_usd),
        "currency": "USD",
        "order_id": str(order_id),
        "url_callback": HELEKET_WEBHOOK_URL,
        "lifetime": 1800,
    }

    json_payload = json.dumps(
        payload, separators=(",", ":")
    )  # важно использовать compact JSON
    base64_data = base64.b64encode(json_payload.encode()).decode()
    sign_raw = base64_data + HELEKET_API_KEY
    sign = hashlib.md5(sign_raw.encode()).hexdigest()

    headers = {
        "merchant": HELEKET_MERCHANT_ID,
        "sign": sign,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.heleket.com/v1/payment", headers=headers, json=payload
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", {}).get("url")
        else:
            print("Failed to create invoice:", resp.status_code, resp.text)
            return None
