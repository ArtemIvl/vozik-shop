import { useEffect, useState } from "react";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";

export default function ConfirmModal({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel
}) {
  const [visible, setVisible] = useState(false);
  useBodyScrollLock(open);

  useEffect(() => {
    if (!open) return undefined;
    const id = window.requestAnimationFrame(() => setVisible(true));
    return () => window.cancelAnimationFrame(id);
  }, [open]);

  if (!open) return null;

  const closeWithAnimation = (callback) => {
    document.activeElement?.blur?.();
    setVisible(false);
    window.setTimeout(callback, 220);
  };

  return (
    <div className={`fixed inset-0 z-[85] flex items-end justify-center px-4 transition duration-200 sm:items-center ${visible ? "bg-black/60 opacity-100" : "bg-black/0 opacity-0"}`}>
      <div className={`relative w-full max-w-sm rounded-t-3xl border border-white/15 bg-tg-surface p-4 shadow-panel transition duration-200 sm:rounded-2xl ${visible ? "translate-y-0" : "translate-y-10"}`}>
        <button
          type="button"
          onClick={() => closeWithAnimation(onCancel)}
          aria-label={cancelLabel}
          className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full border border-white/15 bg-white/5 text-tg-muted"
        >
          X
        </button>
        <h3 className="text-base font-semibold text-tg-text">{title}</h3>
        <p className="mt-2 text-sm text-tg-muted">{message}</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => closeWithAnimation(onCancel)}
            className="rounded-xl border border-white/20 bg-tg-surface-soft px-3 py-2 text-sm text-tg-text"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={() => closeWithAnimation(onConfirm)}
            className="rounded-xl border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-300"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
