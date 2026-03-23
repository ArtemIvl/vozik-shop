import { useEffect, useState } from "react";
import OverlayNotice from "../components/common/OverlayNotice";
import LoadingPulse from "../components/common/LoadingPulse";
import SellStarsOrderModal from "../components/common/SellStarsOrderModal";
import ConfirmModal from "../components/common/ConfirmModal";
import { useCountdown } from "../hooks/useCountdown";
import { openExternalLink } from "../services/tonkeeper";
import {
  cancelMiniAppSellStarsOrder,
  createMiniAppSellStarsOrder,
  getMiniAppPendingSellStarsOrders,
  getMiniAppSellStarsQuote,
  getMiniAppSellStarsInvoice
} from "../services/api";

function openInvoice(url) {
  if (!url) return;
  const tg = window.Telegram?.WebApp;
  if (tg?.openInvoice) {
    tg.openInvoice(url);
    return;
  }
  openExternalLink(url);
}

function CountdownText({ seconds, prefix }) {
  const { formatted } = useCountdown(seconds || 0);
  return <p className="mt-1 text-xs text-star">{prefix}: {formatted}</p>;
}

export default function SellStarsPage({ initData, isActive, onOrdersUpdated, t }) {
  const [starsAmount, setStarsAmount] = useState("50");
  const [loading, setLoading] = useState(false);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [cancellingOrderId, setCancellingOrderId] = useState(null);
  const [error, setError] = useState("");
  const [overlayMessage, setOverlayMessage] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [confirmCancelOrder, setConfirmCancelOrder] = useState(null);
  const [watchedOrderIds, setWatchedOrderIds] = useState([]);
  const [quoteUsdt, setQuoteUsdt] = useState("");
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [loadedOnce, setLoadedOnce] = useState(false);

  const loadPending = async ({ silent = false } = {}) => {
    if (!initData) return;
    try {
      if (!silent) {
        setPendingLoading(true);
      }
      const response = await getMiniAppPendingSellStarsOrders({ init_data: initData });
      const nextOrders = response.orders || [];
      setPendingOrders(nextOrders);
      setSelectedOrder((current) => {
        if (!current) return null;
        return nextOrders.find((item) => item.orderId === current.orderId) || null;
      });
      setWatchedOrderIds((current) => {
        if (current.length === 0) return current;
        const pendingIds = new Set(nextOrders.map((item) => item.orderId));
        const completed = current.some((orderId) => !pendingIds.has(orderId));
        if (completed) {
          setOverlayMessage(t.sellStarsOrderSuccess);
        }
        return current.filter((orderId) => pendingIds.has(orderId));
      });
      setLoadedOnce(true);
      onOrdersUpdated?.();
    } catch {
      setPendingOrders([]);
    } finally {
      if (!silent) {
        setPendingLoading(false);
      }
    }
  };

  useEffect(() => {
    if (!initData || loadedOnce) return;
    loadPending();
  }, [initData, loadedOnce]);

  useEffect(() => {
    if (!isActive || watchedOrderIds.length === 0 || !initData) return undefined;
    const id = window.setInterval(() => {
      loadPending({ silent: true });
    }, 5000);
    return () => window.clearInterval(id);
  }, [initData, isActive, watchedOrderIds]);

  useEffect(() => {
    if (!initData) return undefined;

    const parsed = Number(starsAmount);
    if (!Number.isInteger(parsed) || parsed < 50) {
      setQuoteUsdt("");
      setQuoteLoading(false);
      return undefined;
    }

    let active = true;
    setQuoteLoading(true);
    const timeoutId = window.setTimeout(async () => {
      try {
        const response = await getMiniAppSellStarsQuote({
          init_data: initData,
          stars_amount: parsed
        });
        if (active) {
          setQuoteUsdt(response.payoutUsdt || response.payoutTon || "");
        }
      } catch {
        if (active) {
          setQuoteUsdt("");
        }
      } finally {
        if (active) {
          setQuoteLoading(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      window.clearTimeout(timeoutId);
    };
  }, [initData, starsAmount]);

  const handleCreate = async (event) => {
    event.preventDefault();
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    setError("");
    setSelectedOrder(null);

    const parsed = Number(starsAmount);
    if (!Number.isInteger(parsed) || parsed < 50) {
      return;
    }

    try {
      setLoading(true);
      const result = await createMiniAppSellStarsOrder({
        init_data: initData,
        stars_amount: parsed
      });
      setSelectedOrder(result);
      setWatchedOrderIds((current) => (current.includes(result.orderId) ? current : [...current, result.orderId]));
      openInvoice(result.invoiceUrl);
      await loadPending();
    } catch (requestError) {
      setError(requestError.message || t.sellStarsCreate);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPendingInvoice = async (orderId) => {
    if (!initData) return;
    try {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
      const response = await getMiniAppSellStarsInvoice({
        init_data: initData,
        order_id: orderId
      });
      setWatchedOrderIds((current) => (current.includes(orderId) ? current : [...current, orderId]));
      openInvoice(response.invoiceUrl);
    } catch (requestError) {
      setWatchedOrderIds((current) => current.filter((item) => item !== orderId));
      setError(requestError.message || t.sellStarsPayNow);
    }
  };

  const handleCancelPendingOrder = async (orderId) => {
    if (!initData) return;
    try {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
      setCancellingOrderId(orderId);
      await cancelMiniAppSellStarsOrder({
        init_data: initData,
        order_id: orderId
      });
      setWatchedOrderIds((current) => current.filter((item) => item !== orderId));
      setSelectedOrder((current) => (current?.orderId === orderId ? null : current));
      await loadPending();
    } catch (requestError) {
      setError(requestError.message || t.cancelOrder);
    } finally {
      setCancellingOrderId(null);
    }
  };

  return (
    <section className="space-y-4">
      <OverlayNotice message={overlayMessage} onClose={() => setOverlayMessage("")} closeLabel={t.close} />
      <SellStarsOrderModal
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
        t={t}
      />
      <ConfirmModal
        open={Boolean(confirmCancelOrder)}
        title={t.confirmCancelTitle}
        message={t.confirmCancelMessage}
        confirmLabel={t.cancelOrder}
        cancelLabel={t.close}
        onCancel={() => setConfirmCancelOrder(null)}
        onConfirm={async () => {
          const orderId = confirmCancelOrder;
          setConfirmCancelOrder(null);
          if (orderId) {
            await handleCancelPendingOrder(orderId);
          }
        }}
      />

      <p className="text-xs uppercase tracking-[0.14em] text-tg-muted">{t.sellStars}</p>

      <div className="rounded-3xl border border-white/10 bg-tg-surface p-4">
        <h2 className="text-lg font-semibold text-tg-text">{t.sellStarsCreate}</h2>
        <p className="mt-1 text-sm text-tg-muted">{t.sellStarsHint}</p>

        <form className="mt-4 space-y-4" onSubmit={handleCreate}>
          <div>
            <label className="mb-2 block text-sm text-tg-muted">{t.starsAmountMin}</label>
            <input
              type="number"
              min="50"
              step="1"
              value={starsAmount}
              onChange={(event) => {
                setStarsAmount(event.target.value);
                setError("");
              }}
              className="w-full rounded-xl border border-white/15 bg-tg-surface-soft px-3 py-2 text-tg-text outline-none focus:border-star"
            />
          </div>

          {quoteUsdt ? (
            <div className="rounded-xl border border-[#FFD767]/25 bg-[#FFD767]/10 px-3 py-3">
              <p className="text-xs uppercase tracking-[0.14em] text-[#FFD767]">{t.sellStarsEstimate}</p>
              <p className="mt-1 text-lg font-semibold text-tg-text">
                {quoteLoading ? t.loading : `${quoteUsdt} USDT`}
              </p>
            </div>
          ) : null}

          {error ? <p className="rounded-xl border border-red-400/40 bg-red-400/10 px-3 py-2 text-sm text-red-300">{error}</p> : null}

          <button
            disabled={loading}
            className="w-full rounded-xl bg-[#FFD767] px-4 py-3 font-semibold text-ink-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? t.creatingOrder : t.sellStarsPay}
          </button>
        </form>
      </div>

      <div className="rounded-3xl border border-white/10 bg-tg-surface p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-tg-text">{t.pendingSellStars}</h3>
          <button type="button" onClick={loadPending} className="text-xs text-[#FFD767]">
            {t.refresh}
          </button>
        </div>

        {pendingLoading ? <LoadingPulse label={t.loading} /> : null}
        {!pendingLoading && pendingOrders.length === 0 ? (
          <p className="text-sm text-tg-muted">{t.noPendingSellStars}</p>
        ) : null}

        <div className="space-y-3">
          {pendingOrders.map((order) => (
            <div
              key={order.orderId}
              className="rounded-xl border border-white/10 bg-tg-surface-soft p-3"
            >
              <button
                type="button"
                onClick={() => {
                  document.activeElement?.blur?.();
                  setSelectedOrder(order);
                }}
                className="w-full text-left"
              >
                <p className="text-sm text-tg-text">
                  #{order.orderId} • {order.starsAmount} {t.stars}
                </p>
                <p className="mt-1 text-xs text-tg-muted">{t.sellStarsYouGet}: {order.payoutUsdt || order.payoutTon} USDT</p>
                <CountdownText seconds={order.expiresInSeconds} prefix={t.expiresIn} />
              </button>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleOpenPendingInvoice(order.orderId)}
                  className="rounded-lg border border-[#FFD767]/35 bg-[#FFD767]/15 px-3 py-2 text-xs text-[#FFD767]"
                >
                  {t.sellStarsPayNow}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmCancelOrder(order.orderId)}
                  disabled={cancellingOrderId === order.orderId}
                  className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300 disabled:opacity-60"
                >
                  {cancellingOrderId === order.orderId ? t.sending : t.cancelOrder}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
