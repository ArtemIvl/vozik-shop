const ACCENT_STYLES = {
  star: "border-star/30 bg-star/10 text-star",
  premium: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  gift: "border-fuchsia-400/30 bg-fuchsia-400/10 text-fuchsia-300",
  sell: "border-[#FFD767]/35 bg-[#FFD767]/10 text-[#FFD767]",
  profile: "border-[#FFD767]/35 bg-[#FFD767]/10 text-[#FFD767]"
};

export default function MenuActionCard({ action, onClick, pendingCount = 0 }) {
  const handleClick = () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    onClick(action);
  };

  return (
    <button
      onClick={handleClick}
      className="group relative w-full rounded-2xl border border-white/10 bg-tg-card p-4 text-left transition hover:border-[#FFD767]/45"
    >
      {pendingCount > 0 ? (
        <span className="absolute right-3 top-3 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-semibold text-white">
          {pendingCount > 99 ? "99+" : pendingCount}
        </span>
      ) : null}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-tg-text">{action.title}</h3>
          <p className="mt-1 text-sm text-tg-muted">{action.description}</p>
        </div>
        <span
          className={`inline-flex h-10 w-10 items-center justify-center rounded-xl border text-lg ${ACCENT_STYLES[action.accent]}`}
        >
          {action.icon}
        </span>
      </div>
    </button>
  );
}
