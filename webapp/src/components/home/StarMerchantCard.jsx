export default function StarMerchantCard({ stats, t, onOpenBuyStars }) {
  const starsBought = stats?.purchasedStarsTotal || 0;
  const totalUsdt = stats?.totalEarnedUsdt || stats?.totalEarnedTon || "0.0000";
  const outperformPercent = stats?.outperformPercent ?? 0;
  const scorePoints = stats?.scorePoints ?? 0;

  if (scorePoints <= 0) {
    return (
      <section className="mt-4 rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(255,215,103,0.16),transparent_42%),linear-gradient(180deg,#151a21,#0f1116)] p-5 shadow-panel">
        <p className="text-center text-[11px] uppercase tracking-[0.24em] text-[#FFD767]">{t.mainStatsLabel}</p>
        <h2 className="mt-4 text-center text-xl font-semibold text-tg-text">{t.homeFirstPurchaseTitle}</h2>
        <p className="mt-2 text-center text-sm leading-6 text-tg-muted">{t.homeFirstPurchaseText}</p>
        <button
          type="button"
          onClick={onOpenBuyStars}
          className="mt-5 w-full rounded-2xl bg-[linear-gradient(135deg,#FFD767,#ffefad,#FFD767)] px-4 py-3 text-sm font-semibold text-ink-dark shadow-[0_0_24px_rgba(255,215,103,0.28)] transition hover:scale-[1.01]"
        >
          {t.homeFirstPurchaseCta}
        </button>
      </section>
    );
  }

  return (
    <section className="mt-4 rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(255,215,103,0.12),transparent_42%),linear-gradient(180deg,#151a21,#0f1116)] p-4 shadow-panel">
      <p className="text-center text-[11px] uppercase tracking-[0.24em] text-[#FFD767]">{t.mainStatsLabel}</p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-[1.35rem] border border-[#FFD767]/20 bg-[#171d24] px-3 py-4 text-center">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#FFD767]">{t.starsBoughtLabel}</p>
          <p className="mt-2 text-3xl font-semibold text-tg-text">{starsBought}</p>
        </div>
        <div className="rounded-[1.35rem] border border-[#5fd0ff]/20 bg-[#131c25] px-3 py-4 text-center">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#5fd0ff]">{t.tonEarnedLabel}</p>
          <p className="mt-2 text-3xl font-semibold text-tg-text">{totalUsdt}</p>
          <p className="mt-1 text-xs text-tg-muted">USDT</p>
        </div>
      </div>

      <p className="mt-4 text-center text-sm text-tg-text">
        {t.betterThanPrefix} <span className="font-semibold text-[#FFD767]">{outperformPercent}%</span> {t.betterThanSuffix}
      </p>
    </section>
  );
}
