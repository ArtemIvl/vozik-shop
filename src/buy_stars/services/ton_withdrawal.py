from decimal import Decimal, ROUND_DOWN
import base64

import httpx

from config import (
    TONCENTER_API_KEY,
    TONCENTER_API_URL,
    TON_WALLET_ADDRESS,
    TON_WALLET_MNEMONIC,
    USDT_MASTER_ADDRESS,
    USDT_TRANSFER_GAS_TON,
)


def _ton_to_nanotons(amount_ton: Decimal) -> int:
    return int((Decimal(amount_ton) * Decimal("1000000000")).quantize(Decimal("1"), rounding=ROUND_DOWN))


def _usdt_to_units(amount_usdt: Decimal) -> int:
    return int((Decimal(amount_usdt) * Decimal("1000000")).quantize(Decimal("1"), rounding=ROUND_DOWN))


def _units_to_usdt(amount_units: int | str | Decimal) -> Decimal:
    return (Decimal(str(amount_units)) / Decimal("1000000")).quantize(Decimal("0.000001"))


def _parse_mnemonic_words(raw_value: str) -> list[str]:
    normalized = raw_value.replace(",", " ")
    return [word for word in normalized.split() if word]


def _get_toncenter_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if TONCENTER_API_KEY:
        headers["X-API-Key"] = TONCENTER_API_KEY
    return headers


def _get_toncenter_v3_url() -> str:
    base_url = TONCENTER_API_URL.rstrip("/")
    if base_url.endswith("/api/v2"):
        return f"{base_url[:-len('/api/v2')]}/api/v3"
    if base_url.endswith("/api/v3"):
        return base_url
    return f"{base_url}/api/v3"


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


async def _get_jetton_wallet_address(
    client: httpx.AsyncClient,
    owner_address: str,
    jetton_master_address: str,
) -> tuple[str, int]:
    response = await client.get(
        f"{_get_toncenter_v3_url()}/jetton/wallets",
        headers=_get_toncenter_headers(),
        params={
            "owner_address": owner_address,
            "jetton_address": jetton_master_address,
            "limit": 1,
            "offset": 0,
        },
    )
    response.raise_for_status()
    data = response.json()
    wallets = data.get("jetton_wallets") or data.get("balances") or []
    if not wallets:
        raise RuntimeError("Could not derive USDT jetton wallet address from TON wallet")

    jetton_wallet = wallets[0]
    jetton_wallet_address = jetton_wallet.get("address")
    if not jetton_wallet_address:
        raise RuntimeError("Toncenter returned an empty USDT jetton wallet address")
    return str(jetton_wallet_address), int(jetton_wallet.get("balance") or 0)


async def get_sender_usdt_balance() -> Decimal:
    if not TON_WALLET_ADDRESS:
        raise RuntimeError("TON_WALLET_ADDRESS is not configured")
    if not USDT_MASTER_ADDRESS:
        raise RuntimeError("USDT_MASTER_ADDRESS is not configured")

    async with httpx.AsyncClient(timeout=60.0) as client:
        _, balance_units = await _get_jetton_wallet_address(
            client,
            TON_WALLET_ADDRESS.strip(),
            USDT_MASTER_ADDRESS.strip(),
        )
    return _units_to_usdt(balance_units)


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
        mnemonic_words = _parse_mnemonic_words(TON_WALLET_MNEMONIC)
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


async def send_usdt_withdrawal(address: str, amount_usdt: Decimal) -> tuple[bool, str]:
    if amount_usdt <= 0:
        return False, "Amount must be greater than 0"
    if not TON_WALLET_MNEMONIC:
        return False, "TON_WALLET_MNEMONIC is not configured"
    if not TON_WALLET_ADDRESS:
        return False, "TON_WALLET_ADDRESS is not configured"
    if not USDT_MASTER_ADDRESS:
        return False, "USDT_MASTER_ADDRESS is not configured"

    try:
        from tonsdk.contract.token.ft import JettonWallet
        from tonsdk.contract.wallet import WalletVersionEnum, Wallets
        from tonsdk.utils import Address
    except ImportError:
        return False, "tonsdk is not installed"

    try:
        mnemonic_words = _parse_mnemonic_words(TON_WALLET_MNEMONIC)
        _, _, _, wallet = Wallets.from_mnemonics(
            mnemonic_words,
            WalletVersionEnum.v4r2,
            0,
        )
        derived_address = wallet.address.to_string(True, True, True)
        configured_address = Address(TON_WALLET_ADDRESS).to_string(True, True, True)
        if derived_address != configured_address:
            return False, "Configured TON wallet address does not match TON_WALLET_MNEMONIC"

        jetton_wallet = JettonWallet()
        transfer_body = jetton_wallet.create_transfer_body(
            to_address=Address(address.strip()),
            jetton_amount=_usdt_to_units(Decimal(amount_usdt)),
            forward_amount=1,
            response_address=Address(configured_address),
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            sender_jetton_wallet_address, sender_balance_units = await _get_jetton_wallet_address(
                client,
                configured_address,
                USDT_MASTER_ADDRESS.strip(),
            )
            requested_units = _usdt_to_units(Decimal(amount_usdt))
            if sender_balance_units < requested_units:
                return (
                    False,
                    f"Insufficient USDT balance: available {_units_to_usdt(sender_balance_units):f} USDT, requested {Decimal(amount_usdt):f} USDT",
                )
            seqno = await _get_wallet_seqno(client, configured_address)
            transfer = wallet.create_transfer_message(
                sender_jetton_wallet_address,
                _ton_to_nanotons(Decimal(str(USDT_TRANSFER_GAS_TON))),
                seqno,
                payload=transfer_body,
            )
            tx_hash = await _send_boc(client, transfer["message"].to_boc(False))
            return True, tx_hash
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
