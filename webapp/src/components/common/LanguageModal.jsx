import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";

const LANG_OPTIONS = [
  { code: "en", label: "English" },
  { code: "ru", label: "Русский" },
  { code: "ua", label: "Українська" }
];

export default function LanguageModal({
  open,
  current,
  onClose,
  onSelect,
  closeLabel = "Close",
  title = "Choose language"
}) {
  useBodyScrollLock(open);
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-white/15 bg-tg-surface p-4 shadow-panel">
        <p className="text-sm text-tg-muted">{title}</p>

        <div className="mt-3 space-y-2">
          {LANG_OPTIONS.map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => onSelect(lang.code)}
              className={`w-full rounded-xl border px-3 py-2 text-left text-sm ${
                current === lang.code
                  ? "border-[#FFD767] bg-[#FFD767] text-ink-dark font-semibold"
                  : "border-white/15 bg-tg-surface-soft text-tg-text"
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={onClose}
          className="mt-3 w-full rounded-xl border border-white/20 bg-tg-surface-soft px-3 py-2 text-sm text-tg-text"
        >
          {closeLabel}
        </button>
      </div>
    </div>
  );
}
