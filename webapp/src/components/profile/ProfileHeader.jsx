export default function ProfileHeader({
  userLabel,
  initials,
  welcomeLabel = "Welcome",
  subtitle = "",
  logoSrc = "/bot-logo.jpeg"
}) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-tg-surface px-5 py-5 shadow-panel">
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[#FFD767]/10 blur-2xl" />
      <div className="absolute -left-8 -bottom-10 h-28 w-28 rounded-full bg-star/10 blur-2xl" />

      <div className="relative flex items-center gap-4">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-white/15 bg-gradient-to-br from-vozik/25 to-emerald-500/20 shadow-lg shadow-black/20">
          <img
            src={logoSrc}
            alt="Vozik bot logo"
            className="h-full w-full object-cover"
            onError={(event) => {
              event.currentTarget.style.display = "none";
              const fallback = event.currentTarget.nextElementSibling;
              if (fallback) fallback.style.display = "flex";
            }}
          />
          <span
            style={{ display: "none" }}
            className="h-full w-full items-center justify-center text-xl font-bold text-ink-dark"
          >
            {initials}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-[0.18em] text-tg-muted">Vozik Shop</p>
          <h1 className="mt-1 text-xl font-semibold leading-tight text-tg-text">{welcomeLabel}, {userLabel}</h1>
        </div>
      </div>

      <p className="relative mt-4 text-sm text-tg-muted">{subtitle}</p>
    </section>
  );
}
