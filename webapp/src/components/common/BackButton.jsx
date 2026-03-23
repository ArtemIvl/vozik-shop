export default function BackButton({ onClick, label = "Back" }) {
  const handleClick = () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    onClick();
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-tg-surface-soft px-3 py-2 text-sm text-tg-text"
    >
      <span>←</span>
      <span>{label}</span>
    </button>
  );
}
