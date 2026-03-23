from decimal import Decimal, ROUND_DOWN
import base64

import httpx

from config import TONCENTER_API_KEY, TONCENTER_API_URL, TON_WALLET_ADDRESS, TON_WALLET_MNEMONIC


def _ton_to_nanotons(amount_ton: Decimal) -> int:
    return int((Decimal(amount_ton) * Decimal("1000000000")).quantize(Decimal("1"), rounding=ROUND_DOWN))


def _get_toncenter_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if TONCENTER_API_KEY:
        headers["X-API-Key"] = TONCENTER_API_KEY
    return headers


async def _get_wallet_seqno(client: httpx.AsyncClient, address: str) -> int:
    response = await client.post(
        f"{TONCENTER_API_URL}/runGetMethod",
        headers=_get_toncenter_headers(),
        json={
            "address": address,
            "method": "seqno",
            "stack": [],
        },
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(str(data))

    stack = data.get("result", {}).get("stack") or []
    if not stack:
        return 0

    _, seqno_hex = stack[0]
    return int(seqno_hex, 16)


async def _send_boc(client: httpx.AsyncClient, boc: bytes) -> str:
    response = await client.post(
        f"{TONCENTER_API_URL}/sendBoc",
        headers=_get_toncenter_headers(),
        json={
            "boc": base64.b64encode(boc).decode(),
        },
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(str(data))

    return str(data.get("result") or "submitted")


async def send_ton_withdrawal(address: str, amount_ton: Decimal) -> tuple[bool, str]:
    if amount_ton <= 0:
        return False, "Amount must be greater than 0"
    if not TON_WALLET_MNEMONIC:
        return False, "TON_WALLET_MNEMONIC is not configured"
    if not TON_WALLET_ADDRESS:
        return False, "TON_WALLET_ADDRESS is not configured"

    try:
        from tonsdk.contract.wallet import WalletVersionEnum, Wallets
        from tonsdk.utils import Address
    except ImportError:
        return False, "tonsdk is not installed"

    try:
        mnemonic_words = TON_WALLET_MNEMONIC.split(',')
        _, _, _, wallet = Wallets.from_mnemonics(
            mnemonic_words,
            WalletVersionEnum.v4r2,
            0,
        )
        derived_address = wallet.address.to_string(True, True, True)
        configured_address = Address(TON_WALLET_ADDRESS).to_string(True, True, True)
        if derived_address != configured_address:
            return False, "Configured TON wallet address does not match TON_WALLET_MNEMONIC"

        async with httpx.AsyncClient(timeout=60.0) as client:
            seqno = await _get_wallet_seqno(client, configured_address)
            transfer = wallet.create_transfer_message(
                address.strip(),
                _ton_to_nanotons(Decimal(amount_ton)),
                seqno,
                payload="withdrawal",
            )
            tx_hash = await _send_boc(client, transfer["message"].to_boc(False))
            return True, tx_hash
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
