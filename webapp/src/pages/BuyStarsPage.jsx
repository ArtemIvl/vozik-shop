import { useEffect, useMemo, useState } from "react";
import SegmentedSwitch from "../components/common/SegmentedSwitch";
import { cancelMiniAppOrder, createMiniAppStarsOrder, getMiniAppOrderPaymentLink, getMiniAppPendingOrders } from "../services/api";
import { openTonkeeper } from "../services/tonkeeper";
import OverlayNotice from "../components/common/OverlayNotice";
import OrderDetailsModal from "../components/common/OrderDetailsModal";
import LoadingPulse from "../components/common/LoadingPulse";
import ConfirmModal from "../components/common/ConfirmModal";
import { useCountdown } from "../hooks/useCountdown";

function CountdownText({ seconds, prefix }) {
  const { formatted } = useCountdown(seconds || 0);
  return <p className="mt-1 text-xs text-star">{prefix}: {formatted}</p>;
}

export default function BuyStarsPage({ initData, tgUser, sendData, onOrdersUpdated, t }) {
  const [recipientMode, setRecipientMode] = useState("self");
  const [username, setUsername] = useState("");
  const [starsAmount, setStarsAmount] = useState("50");
  const [paymentMethod, setPaymentMethod] = useState("TON");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pendingOrders, setPendingOrders] = useState([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [overlayMessage, setOverlayMessage] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [confirmCancelOrder, setConfirmCancelOrder] = useState(null);
  const [watchedOrderIds, setWatchedOrderIds] = useState([]);

  const selfUsername = tgUser?.username || "";

  const targetUsername = useMemo(() => {
    if (recipientMode === "self") return selfUsername;
    return username.trim().replace(/^@/, "");
  }, [recipientMode, selfUsername, username]);

  const canSubmit = Number(starsAmount) >= 50 && !!targetUsername && !loading;

  const loadPendingOrders = async () => {
    if (!initData) return;
    try {
      setPendingLoading(true);
      const response = await getMiniAppPendingOrders({
        init_data: initData,
        order_type: "stars"
      });
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
          setOverlayMessage(t.starsOrderSuccess);
        }
        return current.filter((orderId) => pendingIds.has(orderId));
      });
      onOrdersUpdated?.();
    } catch {
      setPendingOrders([]);
    } finally {
      setPendingLoading(false);
    }
  };

  useEffect(() => {
    loadPendingOrders();
  }, [initData]);

  useEffect(() => {
    if (watchedOrderIds.length === 0 || !initData) return undefined;
    const id = window.setInterval(() => {
      loadPendingOrders();
    }, 5000);
    return () => window.clearInterval(id);
  }, [initData, watchedOrderIds]);

  const handleCreateOrder = async (event) => {
    event.preventDefault();
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    setError("");
    setSelectedOrder(null);

    if (!initData) {
      setError(t.authMissing);
      return;
    }

    if (!targetUsername) {
      setError(t.enterUsernameError);
      return;
    }

    const parsedStars = Number(starsAmount);
    if (!Number.isInteger(parsedStars) || parsedStars < 50) {
      setError(t.minStarsError);
      return;
    }

    try {
      setLoading(true);
      const result = await createMiniAppStarsOrder({
        init_data: initData,
        for_self: recipientMode === "self",
        to_username: recipientMode === "other" ? targetUsername : null,
        stars_amount: parsedStars,
        payment_method: paymentMethod
      });
      setSelectedOrder(result);
      sendData({ event: "miniapp_order_created", orderId: result.orderId, type: "stars" });
      await loadPendingOrders();
    } catch (requestError) {
      setError(requestError.message || t.createOrder);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!initData) return;
    try {
      await cancelMiniAppOrder({
        init_data: initData,
        order_id: orderId
      });
      setWatchedOrderIds((current) => current.filter((item) => item !== orderId));
      setSelectedOrder((current) => (current?.orderId === orderId ? null : current));
      await loadPendingOrders();
    } catch (requestError) {
      setError(requestError.message || t.cancelOrder);
    }
  };

  const handlePayOrder = async (event, order) => {
    event.preventDefault();
    event.stopPropagation();
    if (!initData) return;

    try {
      setWatchedOrderIds((current) => (current.includes(order.orderId) ? current : [...current, order.orderId]));
      if (order.paymentType === "TON") {
        openTonkeeper({
          deepLink: order.tonkeeperUrl,
          webLink: order.tonkeeperWebUrl
        });
        return;
      }

      const response = await getMiniAppOrderPaymentLink({
        init_data: initData,
        order_id: order.orderId
      });
      if (response.invoiceUrl) {
        window.open(response.invoiceUrl, "_blank", "noopener,noreferrer");
      }
    } catch (requestError) {
      setWatchedOrderIds((current) => current.filter((item) => item !== order.orderId));
      setError(requestError.message || t.openHeleket);
    }
  };

  return (
    <section className="space-y-4">
      <OverlayNotice message={overlayMessage} onClose={() => setOverlayMessage("")} closeLabel={t.close} />
      <OrderDetailsModal
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
            await handleCancelOrder(orderId);
          }
        }}
      />
      <p className="text-xs uppercase tracking-[0.14em] text-tg-muted">{t.buyStars}</p>

      <div className="rounded-3xl border border-white/10 bg-tg-surface p-4">
        <h2 className="text-lg font-semibold text-tg-text">{t.createOrderTitle}</h2>
        <p className="mt-1 text-sm text-tg-muted">{t.starsFlowHint}</p>

        <form className="mt-4 space-y-4" onSubmit={handleCreateOrder}>
          <div>
            <label className="mb-2 block text-sm text-tg-muted">{t.whoStarsFor}</label>
            <SegmentedSwitch
              value={recipientMode}
              onChange={setRecipientMode}
              options={[
                { value: "self", label: t.forMyself },
                { value: "other", label: t.forOther }
              ]}
            />
          </div>

          {recipientMode === "other" ? (
            <div>
              <label className="mb-2 block text-sm text-tg-muted">{t.targetUsername}</label>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="@username"
                className="w-full rounded-xl border border-white/15 bg-tg-surface-soft px-3 py-2 text-tg-text outline-none focus:border-[#FFD767]"
              />
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 bg-tg-surface-soft px-3 py-2 text-sm text-tg-muted">
              {t.yourAccount}: <span className="text-tg-text">@{selfUsername || "unknown"}</span>
            </div>
          )}

          <div>
            <label className="mb-2 block text-sm text-tg-muted">{t.starsAmountMin}</label>
            <input
              type="number"
              min="50"
              step="1"
              value={starsAmount}
              onChange={(event) => setStarsAmount(event.target.value)}
              className="w-full rounded-xl border border-white/15 bg-tg-surface-soft px-3 py-2 text-tg-text outline-none focus:border-star"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-tg-muted">{t.paymentMethod}</label>
            <SegmentedSwitch
              value={paymentMethod}
              onChange={setPaymentMethod}
              options={[
                { value: "TON", label: "TON" },
                { value: "USDT", label: "USDT / crypto" }
              ]}
            />
          </div>

          {error ? <p className="rounded-xl border border-red-400/40 bg-red-400/10 px-3 py-2 text-sm text-red-300">{error}</p> : null}

          <button
            disabled={!canSubmit}
            className="w-full rounded-xl bg-[#FFD767] px-4 py-3 font-semibold text-ink-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? t.creatingOrder : t.createOrder}
          </button>
        </form>
      </div>

      <div className="rounded-3xl border border-white/10 bg-tg-surface p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-tg-text">{t.pendingStars}</h3>
          <button
            type="button"
            onClick={loadPendingOrders}
            className="text-xs text-[#FFD767]"
          >
            {t.refresh}
          </button>
        </div>

        {pendingLoading ? <LoadingPulse label={t.loading} /> : null}
        {!pendingLoading && pendingOrders.length === 0 ? (
          <p className="text-sm text-tg-muted">{t.noPendingStars}</p>
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
                  #{order.orderId} • {order.starsAmount} {t.stars} • @{order.toUsername}
                </p>
                <p className="mt-1 text-xs text-tg-muted">
                  {order.paymentType} • {order.priceTon ? `${order.priceTon} TON` : `${order.priceUsdt} USD`} • {order.status}
                </p>
                <CountdownText seconds={order.expiresInSeconds} prefix={t.expiresIn} />
              </button>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {order.paymentType === "TON" ? (
                  <a
                    href={order.tonkeeperWebUrl || order.tonkeeperUrl}
                    onClick={(event) => handlePayOrder(event, order)}
                    className="rounded-lg border border-[#0098EA]/40 bg-[#0098EA]/15 px-2 py-2 text-center text-xs text-[#4DB8FF]"
                  >
                    {t.openTonkeeper}
                  </a>
                ) : (
                  <button
                    type="button"
                    onClick={(event) => handlePayOrder(event, order)}
                    className="rounded-lg border border-[#FFD767]/35 bg-[#FFD767]/15 px-2 py-2 text-center text-xs text-[#FFD767]"
                  >
                    {t.pay}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setConfirmCancelOrder(order.orderId)}
                  className="rounded-lg border border-red-400/30 bg-red-400/10 px-2 py-2 text-xs text-red-300"
                >
                  {t.cancelOrder}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
