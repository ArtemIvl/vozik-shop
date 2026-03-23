export default function SegmentedSwitch({ value, options, onChange }) {
  const handleSelect = (nextValue) => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
    onChange(nextValue);
  };

  return (
    <div className="grid grid-cols-2 rounded-xl border border-white/15 bg-tg-surface-soft p-1">
      {options.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => handleSelect(option.value)}
            className={`rounded-lg px-3 py-2 text-sm transition ${
              active
                ? "bg-[#FFD767] text-ink-dark font-semibold"
                : "text-tg-muted hover:text-tg-text"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
