export default function AppShell({ children, bottomNav = null }) {
  return (
    <main className="mx-auto h-[100dvh] w-full max-w-md text-tg-text">
      <div className="h-full overflow-y-auto px-4 pb-24 pt-5">
        {children}
      </div>
      {bottomNav}
    </main>
  );
}
