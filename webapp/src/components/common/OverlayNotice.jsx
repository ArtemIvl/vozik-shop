import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";

export default function OverlayNotice({ message, onClose, closeLabel = "Close" }) {
  useBodyScrollLock(Boolean(message));
  if (!message) return null;

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-white/15 bg-tg-surface p-4 shadow-panel">
        <p className="text-sm text-tg-text">{message}</p>
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
