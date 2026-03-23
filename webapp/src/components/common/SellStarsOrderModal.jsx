import { useEffect, useState } from "react";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { useCountdown } from "../../hooks/useCountdown";

export default function SellStarsOrderModal({ order, onClose, t }) {
  const [visible, setVisible] = useState(false);
  useBodyScrollLock(Boolean(order));
  const { formatted: expiresIn } = useCountdown(order?.expiresInSeconds || 0);

  useEffect(() => {
    if (!order) return undefined;
    const id = window.requestAnimationFrame(() => setVisible(true));
    return () => window.cancelAnimationFrame(id);
  }, [order]);

  if (!order) return null;

  const closeWithAnimation = () => {
    document.activeElement?.blur?.();
    setVisible(false);
    window.setTimeout(() => onClose(), 220);
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
          {t.order} #{order.orderId} • {order.starsAmount} {t.stars}
        </p>
        <p className="mt-1 text-xs text-star">{t.expiresIn}: {expiresIn}</p>

        <div className="mt-3 rounded-xl border border-white/10 bg-tg-surface-soft p-3">
          <p className="text-xs text-tg-muted">{t.sellStarsYouGet}</p>
          <p className="text-sm text-tg-text">{order.payoutTon} TON</p>
        </div>

      </div>
    </div>
  );
}
