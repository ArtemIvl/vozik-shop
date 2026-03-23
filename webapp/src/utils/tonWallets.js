const RAW_TON_ADDRESS_RE = /^(?:-1|0):[0-9a-fA-F]{64}$/;
const USER_FRIENDLY_TON_ADDRESS_RE = /^[A-Za-z0-9_-]{48}$/;

export function isLikelyTonWallet(value) {
  const normalized = (value || "").trim();
  return RAW_TON_ADDRESS_RE.test(normalized) || USER_FRIENDLY_TON_ADDRESS_RE.test(normalized);
}
