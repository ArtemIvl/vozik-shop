import { useEffect, useState } from "react";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { useCountdown } from "../../hooks/useCountdown";

function copyText(value) {
  if (!value) return;
  window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
  navigator.clipboard.writeText(String(value)).catch(() => null);
}

export default function OrderDetailsModal({ order, onClose, t }) {
  const [visible, setVisible] = useState(false);
  const [copiedField, setCopiedField] = useState("");
  useBodyScrollLock(Boolean(order));
  const { formatted: expiresIn } = useCountdown(order?.expiresInSeconds || 0);

  useEffect(() => {
    if (!order) return undefined;
    const id = window.requestAnimationFrame(() => setVisible(true));
    return () => window.cancelAnimationFrame(id);
  }, [order]);

  useEffect(() => {
    if (!copiedField) return undefined;
    const id = window.setTimeout(() => setCopiedField(""), 1600);
    return () => window.clearTimeout(id);
  }, [copiedField]);

  if (!order) return null;

  const quantityLabel = order.starsAmount
    ? `${order.starsAmount} ${t.stars}`
    : `${order.months} ${t.months}`;
  const paymentAmountLabel = order.priceTon ? `${order.priceTon} TON` : `${order.priceUsdt || "-"} USDT`;

  const closeWithAnimation = () => {
    document.activeElement?.blur?.();
    setVisible(false);
    window.setTimeout(() => onClose(), 220);
  };

  const handleCopy = (field, value) => {
    copyText(value);
    setCopiedField(field);
  };

  return (
    <div className={`fixed inset-0 z-[70] flex items-end justify-center px-4 transition duration-200 sm:items-center ${visible ? "bg-black/60 opacity-100" : "bg-black/0 opacity-0"}`}>
      <div className={`relative mb-0 w-full max-w-sm rounded-t-3xl border border-white/15 bg-tg-surface p-4 shadow-panel transition duration-200 sm:mb-0 sm:rounded-2xl ${visible ? "translate-y-0" : "translate-y-10"}`}>
        <button
          type="button"
          onClick={closeWithAnimation}
          aria-label={t.close}
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full border border-white/15 bg-white/5 text-tg-muted transition hover:text-tg-text"
        >
          X
        </button>
        <h3 className="text-base font-semibold text-tg-text">{t.orderDetails}</h3>
        <p className="mt-1 text-sm text-tg-muted">
          {t.order} #{order.orderId} • {t.recipient}: @{order.toUsername}
        </p>
        <p className="mt-1 text-xs text-star">{t.expiresIn}: {expiresIn}</p>

        <div className="mt-3 space-y-3">
          <div className="rounded-xl border border-white/10 bg-tg-surface-soft p-3">
            <p className="text-xs text-tg-muted">{t.amount}</p>
            <p className="text-sm text-tg-text">{paymentAmountLabel}</p>
            {order.priceTon || order.priceUsdt ? (
              <button
                type="button"
                onClick={() => handleCopy("amount", order.priceTon || order.priceUsdt)}
                className="mt-2 text-xs text-[#FFD767]"
              >
                {copiedField === "amount" ? t.copied : t.copyAmount}
              </button>
            ) : null}
          </div>
          <div className="rounded-xl border border-white/10 bg-tg-surface-soft p-3">
            <p className="text-xs text-tg-muted">{t.quantity}</p>
            <p className="text-sm text-tg-text">{quantityLabel}</p>
          </div>
          {order.walletAddress ? (
            <div className="rounded-xl border border-white/10 bg-tg-surface-soft p-3">
              <p className="text-xs text-tg-muted">{t.wallet}</p>
              <p className="break-all text-sm text-tg-text">{order.walletAddress}</p>
              <button
                type="button"
                onClick={() => handleCopy("wallet", order.walletAddress)}
                className="mt-2 text-xs text-[#FFD767]"
              >
                {copiedField === "wallet" ? t.copied : t.copyWallet}
              </button>
            </div>
          ) : null}
          <div className="rounded-xl border border-white/10 bg-tg-surface-soft p-3">
            <p className="text-xs text-tg-muted">{t.memoRequired}</p>
            <p className="text-sm text-star">{order.memo || "-"}</p>
            {order.memo ? (
              <button
                type="button"
                onClick={() => handleCopy("memo", order.memo)}
                className="mt-2 text-xs text-[#FFD767]"
              >
                {copiedField === "memo" ? t.copied : t.copyMemo}
              </button>
            ) : null}
          </div>
        </div>

      </div>
    </div>
  );
}
