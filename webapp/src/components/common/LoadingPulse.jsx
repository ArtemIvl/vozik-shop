export default function LoadingPulse({ label = "Loading..." }) {
  return (
    <div className="flex w-full items-center justify-center gap-2 py-3 text-center text-sm text-tg-muted">
      <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-[#FFD767]" />
      <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-star [animation-delay:120ms]" />
      <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-sky-300 [animation-delay:240ms]" />
      <span>{label}</span>
    </div>
  );
}
