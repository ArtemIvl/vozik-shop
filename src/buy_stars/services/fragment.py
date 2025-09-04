import httpx
from config import FRAGMENT_JWT_KEY

FRAGMENT_API_BASE_URL = "https://api.fragment-api.com/v1"

HEADERS = {
    "Authorization": f"JWT {FRAGMENT_JWT_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async def buy_stars(username: str, quantity: int, show_sender: bool = False) -> bool:
    print("trying to buy")
    if quantity < 50:
        print("❌ Fragment requires minimum 50 stars to buy.")
        return False

    payload = {
        "username": username.lstrip("@"),
        "quantity": quantity,
        "show_sender": show_sender
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{FRAGMENT_API_BASE_URL}/order/stars/",
                headers=HEADERS,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ Stars purchased:", data)
                return True
            else:
                print(f"❌ Fragment API error: {response.status_code} — {response.text}")
                return False

    except Exception as e:
        print(f"❗ Exception occurred while purchasing stars: {type(e).__name__} — {e}")
        return False
    

async def buy_premium(username: str, months: int, show_sender: bool = False) -> bool:
    print("trying to buy premium")
    if months not in (3, 6, 12):
        print("❌ Invalid premium subscription duration. Must be 3, 6, or 12 months.")
        return False

    payload = {
        "username": username.lstrip("@"),
        "months": months,
        "show_sender": show_sender
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{FRAGMENT_API_BASE_URL}/order/premium/",
                headers=HEADERS,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ Premium purchased:", data)
                return True
            else:
                print(f"❌ Fragment API error: {response.status_code} — {response.text}")
                return False

    except Exception as e:
        print(f"❗ Exception occurred while purchasing premium: {type(e).__name__} — {e}")
        return False