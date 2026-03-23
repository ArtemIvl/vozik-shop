import MenuActionCard from "./MenuActionCard";

export default function MainMenuSection({ actions, onActionClick, pendingCounts, title = "Main Menu" }) {
  return (
    <section className="mt-5">
      <div className="mb-3 flex items-center gap-2 text-tg-muted">
        <span className="h-2 w-2 rounded-full bg-[#FFD767]" />
        <p className="text-xs uppercase tracking-[0.14em]">{title}</p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {actions.map((action) => (
          <MenuActionCard
            key={action.id}
            action={action}
            onClick={onActionClick}
            pendingCount={pendingCounts?.[action.id] || 0}
          />
        ))}
      </div>
    </section>
  );
}
