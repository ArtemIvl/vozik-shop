import { useEffect, useState } from "react";
import OverlayNotice from "../components/common/OverlayNotice";
import LoadingPulse from "../components/common/LoadingPulse";
import { createMiniAppWithdraw, getMiniAppProfile, setMiniAppWallet } from "../services/api";
import { isLikelyTonWallet } from "../utils/tonWallets";

function copyText(value) {
  if (!value) return;
  window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
  navigator.clipboard.writeText(String(value)).catch(() => null);
}

function StatTile({ label, value, accent = "gold", suffix = "" }) {
  const accentClasses = {
    gold: "border-[#FFD767]/20 bg-[#1d1a12]",
    cyan: "border-sky-300/20 bg-[#131c25]",
    emerald: "border-emerald-300/20 bg-[#13211d]",
    rose: "border-rose-300/20 bg-[#21171a]"
  };

  return (
    <div className={`rounded-[1.4rem] border p-4 ${accentClasses[accent] || accentClasses.gold}`}>
      <p className="text-[11px] uppercase tracking-[0.16em] text-tg-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-tg-text">
        {value}
        {suffix ? <span className="ml-1 text-sm text-tg-muted">{suffix}</span> : null}
      </p>
    </div>
  );
}

export default function ProfilePage({ initData, t }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [amount, setAmount] = useState("0.5");
  const [wallet, setWallet] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [savingWallet, setSavingWallet] = useState(false);
  const [overlayMessage, setOverlayMessage] = useState("");
  const [linkCopied, setLinkCopied] = useState(false);

  const loadProfile = async () => {
    if (!initData) return;
    try {
      setLoading(true);
      setError("");
      const response = await getMiniAppProfile({ init_data: initData });
      setProfile(response);
      setWallet(response.savedTonWallet || "");
    } catch (requestError) {
      setError(requestError.message || t.profile);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [initData]);

  const handleWithdraw = async (event) => {
    event.preventDefault();
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");

    if (!isLikelyTonWallet(wallet)) {
      setOverlayMessage(t.invalidWallet);
      return;
    }

    try {
      setSubmitting(true);
      const response = await createMiniAppWithdraw({
        init_data: initData,
        amount,
        wallet
      });
      setOverlayMessage(response.message || "Withdrawal request sent");
      setAmount("0.5");
      await loadProfile();
    } catch (requestError) {
      setOverlayMessage(requestError.message || t.withdraw);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveWallet = async () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    if (!isLikelyTonWallet(wallet)) {
      setOverlayMessage(t.invalidWallet);
      return;
    }
    try {
      setSavingWallet(true);
      const response = await setMiniAppWallet({
        init_data: initData,
        wallet
      });
      setOverlayMessage(response.message || t.walletSaved);
      await loadProfile();
    } catch (requestError) {
      setOverlayMessage(requestError.message || t.saveWallet);
    } finally {
      setSavingWallet(false);
    }
  };

  return (
    <section className="space-y-4">
      <OverlayNotice message={overlayMessage} onClose={() => setOverlayMessage("")} closeLabel={t.close} />

      <p className="text-xs uppercase tracking-[0.14em] text-tg-muted">{t.profile}</p>

      {loading && !profile ? (
        <div className="rounded-[2rem] border border-white/10 bg-tg-surface p-5 shadow-panel">
          <LoadingPulse label={t.loading} />
        </div>
      ) : null}

      {error ? (
        <div className="rounded-2xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      {profile ? (
        <>
          <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(255,215,103,0.16),transparent_40%),linear-gradient(180deg,#171c24,#0f1116)] p-5 shadow-panel">
            <div className="absolute -right-8 top-0 h-28 w-28 rounded-full bg-[#FFD767]/10 blur-3xl" />
            <div className="absolute -left-6 bottom-0 h-24 w-24 rounded-full bg-sky-300/10 blur-3xl" />

            <div className="relative">
              <p className="text-[11px] uppercase tracking-[0.22em] text-[#FFD767]">{t.balance}</p>
              <p className="mt-2 text-4xl font-semibold leading-none text-tg-text">
                {profile.referralBalanceTon}
                <span className="ml-2 text-base text-[#FFD767]">TON</span>
              </p>
              <p className="mt-3 text-sm text-tg-muted">
                {t.totalEarned}: <span className="text-tg-text">{profile.referralTotalEarnedTon} TON</span>
              </p>

              <div className="mt-5 grid grid-cols-2 gap-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
                  <p className="text-[11px] text-tg-muted">{t.referrals}</p>
                  <p className="mt-1 text-xl font-semibold text-tg-text">{profile.referralCount}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
                  <p className="text-[11px] text-tg-muted">{t.activeReferrals}</p>
                  <p className="mt-1 text-xl font-semibold text-tg-text">{profile.activeReferralCount}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
                  <p className="text-[11px] text-tg-muted">{t.referralEarned}</p>
                  <p className="mt-1 text-xl font-semibold text-tg-text">{profile.referralEarnedTon}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
                  <p className="text-[11px] text-tg-muted">{t.commission}</p>
                  <p className="mt-1 text-xl font-semibold text-tg-text">{profile.referralCommissionPercent}%</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-tg-surface p-4 shadow-panel">
            <div className="mb-3">
              <h3 className="text-base font-semibold text-tg-text">{t.mainStatsLabel}</h3>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <StatTile label={t.totalOrders} value={profile.totalOrdersCount} accent="gold" />
              <StatTile label={t.purchasedStars} value={profile.purchasedStarsTotal} accent="cyan" />
              <StatTile label={t.exchangedStars} value={profile.exchangedStarsTotal} accent="emerald" />
              <StatTile label={t.receivedTon} value={profile.receivedTonTotal} accent="rose" suffix="TON" />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-[2rem] border border-white/10 bg-tg-surface p-4 shadow-panel">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-tg-text">{t.savedWallet}</h3>
              </div>
              <p className="mt-3 break-all rounded-2xl border border-white/10 bg-tg-surface-soft px-3 py-3 text-sm text-tg-text">
                {profile.savedTonWallet || "—"}
              </p>
              <p className="mt-3 text-xs leading-5 text-tg-muted">{t.savedWalletHint}</p>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-tg-surface p-4 shadow-panel">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-tg-text">{t.referralLink}</h3>
                <button
                  type="button"
                  onClick={() => {
                    copyText(profile.referralLink);
                    setLinkCopied(true);
                    window.setTimeout(() => setLinkCopied(false), 1800);
                  }}
                  className="rounded-full border border-[#FFD767]/25 bg-[#FFD767]/10 px-3 py-1 text-[11px] uppercase tracking-[0.14em] text-[#FFD767]"
                >
                  {linkCopied ? t.referralCopied : t.copyReferral}
                </button>
              </div>
              <p className="mt-3 break-all rounded-2xl border border-[#FFD767]/20 bg-[#FFD767]/8 px-3 py-3 text-sm text-[#FFD767]">
                {profile.referralLink}
              </p>
            </div>
          </div>
        </>
      ) : null}

      <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,#18222d,#131b25)] p-4 shadow-panel">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-tg-text">{t.withdraw}</h3>
            <p className="mt-1 text-sm text-tg-muted">{profile?.minWithdrawalTon || "0.5"} TON+</p>
          </div>
        </div>

        <form className="mt-4 space-y-3" onSubmit={handleWithdraw}>
          <div className="grid grid-cols-[1fr_auto] gap-3">
            <div>
              <label className="mb-1 block text-sm text-tg-muted">{t.amountTon}</label>
              <input
                type="number"
                min="0.5"
                step="0.1"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                className="w-full rounded-2xl border border-white/15 bg-tg-surface-soft px-3 py-3 text-tg-text outline-none focus:border-[#FFD767]"
              />
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={() => setAmount(profile?.referralBalanceTon || "0.5")}
                className="rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-tg-text"
              >
                Max
              </button>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm text-tg-muted">{t.walletAddress}</label>
            <input
              value={wallet}
              onChange={(event) => setWallet(event.target.value)}
              placeholder="UQ..."
              className="w-full rounded-2xl border border-white/15 bg-tg-surface-soft px-3 py-3 text-tg-text outline-none focus:border-[#FFD767]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={handleSaveWallet}
              disabled={savingWallet || !wallet.trim()}
              className="rounded-2xl border border-[#FFD767]/35 bg-[#FFD767]/12 px-3 py-2.5 text-sm font-semibold text-[#FFD767] disabled:opacity-60"
            >
              {savingWallet ? t.sending : t.saveWallet}
            </button>

            <button
              disabled={submitting}
              className="rounded-2xl bg-[#FFD767] px-3 py-2.5 text-sm font-semibold text-ink-dark disabled:opacity-60"
            >
              {submitting ? t.sending : t.withdraw}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
