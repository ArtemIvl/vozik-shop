const NAV_ITEMS = [
  { id: "menu", icon: "🏠", labelKey: "mainMenu" },
  { id: "buy_stars", icon: "⭐", labelKey: "buyStars" },
  { id: "buy_premium", icon: "💎", labelKey: "buyPremium" },
  { id: "sell_stars", icon: "💸", labelKey: "sellStars" },
  { id: "profile", icon: "👤", labelKey: "profile" }
];

export default function BottomNav({ activePage, onSelect, t, pendingCounts }) {
  return (
    <nav className="absolute bottom-2 left-2 right-2 z-50 rounded-2xl border border-white/10 bg-tg-surface/95 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur">
      <div className="grid grid-cols-5 gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = activePage === item.id;
          const badgeCount =
            item.id === "buy_stars"
              ? pendingCounts?.buy_stars || 0
              : item.id === "buy_premium"
                ? pendingCounts?.buy_tg_premium || 0
                : item.id === "sell_stars"
                  ? pendingCounts?.sell_stars || 0
                  : 0;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                onSelect(item.id);
              }}
              className={`relative rounded-xl px-1 py-2 text-center transition ${
                isActive ? "bg-[#FFD767]/18 text-[#FFD767]" : "text-tg-muted"
              }`}
            >
              {badgeCount > 0 ? (
                <span className="absolute right-2 top-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
                  {badgeCount > 99 ? "99+" : badgeCount}
                </span>
              ) : null}
              <div className="text-xl leading-none">{item.icon}</div>
              <div className="mt-0.5 truncate text-[10px]">{t[item.labelKey]}</div>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
