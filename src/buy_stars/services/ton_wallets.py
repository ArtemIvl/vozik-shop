import re

RAW_TON_ADDRESS_RE = re.compile(r"^(?:-1|0):[0-9a-fA-F]{64}$")
USER_FRIENDLY_TON_ADDRESS_RE = re.compile(r"^[A-Za-z0-9_-]{48}$")


def normalize_ton_wallet(wallet: str) -> str:
    value = (wallet or "").strip()
    if not value:
        raise ValueError("Wallet is required")

    if not (
        RAW_TON_ADDRESS_RE.fullmatch(value)
        or USER_FRIENDLY_TON_ADDRESS_RE.fullmatch(value)
    ):
        raise ValueError("Invalid TON wallet address")

    try:
        from tonsdk.utils import Address
    except ImportError as exc:
        raise RuntimeError("tonsdk is not installed") from exc

    try:
        Address(value)
        return value
    except Exception as exc:
        raise ValueError("Invalid TON wallet address") from exc
