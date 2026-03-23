export default function AppFooter({ supportUrl, supportLabel, languageLabel, onOpenLanguage }) {
  return (
    <footer className="mt-5 flex items-center justify-between rounded-2xl border border-white/10 bg-tg-surface-soft px-4 py-3">
      <a
        href={supportUrl}
        target="_blank"
        rel="noreferrer"
        className="text-sm text-[#FFD767] underline-offset-2 hover:underline"
      >
        {supportLabel}
      </a>

      <button
        type="button"
        onClick={onOpenLanguage}
        className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-tg-surface text-tg-text"
        aria-label={languageLabel}
        title={languageLabel}
      >
        🌐
      </button>
    </footer>
  );
}
