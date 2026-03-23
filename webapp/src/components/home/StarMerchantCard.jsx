export default function StarMerchantCard({ stats, t }) {
  const starsBought = stats?.purchasedStarsTotal || 0;
  const totalTon = stats?.totalEarnedTon || "0.0000";
  const outperformPercent = stats?.outperformPercent ?? 0;

  return (
    <section className="mt-4 rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(255,215,103,0.12),transparent_42%),linear-gradient(180deg,#151a21,#0f1116)] p-4 shadow-panel">
      <p className="text-center text-[11px] uppercase tracking-[0.24em] text-[#FFD767]">{t.mainStatsLabel}</p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-[1.35rem] border border-[#FFD767]/20 bg-[#171d24] px-3 py-4 text-center">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#FFD767]">{t.starsBoughtLabel}</p>
          <p className="mt-2 text-3xl font-semibold text-tg-text">{starsBought}</p>
        </div>
        <div className="rounded-[1.35rem] border border-[#5fd0ff]/20 bg-[#131c25] px-3 py-4 text-center">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[#5fd0ff]">{t.tonEarnedLabel}</p>
          <p className="mt-2 text-3xl font-semibold text-tg-text">{totalTon}</p>
          <p className="mt-1 text-xs text-tg-muted">TON</p>
        </div>
      </div>

      <p className="mt-4 text-center text-sm text-tg-text">
        {t.betterThanPrefix} <span className="font-semibold text-[#FFD767]">{outperformPercent}%</span> {t.betterThanSuffix}
      </p>
      <p className="mt-1 text-center text-xs text-tg-muted">{t.tonEarnedHint}</p>
    </section>
  );
}
