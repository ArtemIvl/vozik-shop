import { useEffect, useState } from "react";
import ProfileHeader from "../components/profile/ProfileHeader";
import AppFooter from "../components/layout/AppFooter";
import LoadingPulse from "../components/common/LoadingPulse";
import StarMerchantCard from "../components/home/StarMerchantCard";
import { getMiniAppProfile } from "../services/api";

export default function MainMenuPage({
  userLabel,
  initials,
  initData,
  t,
  onOpenLanguage,
  onOpenBuyStars,
  supportUrl,
  onOpenGift
}) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initData) return;
    let active = true;

    const loadStats = async () => {
      try {
        setLoading(true);
        const response = await getMiniAppProfile({ init_data: initData });
        if (active) setStats(response);
      } catch {
        if (active) setStats(null);
      } finally {
        if (active) setLoading(false);
      }
    };

    loadStats();
    return () => {
      active = false;
    };
  }, [initData]);

  return (
    <>
      <ProfileHeader
        userLabel={userLabel}
        initials={initials}
        welcomeLabel={t.welcome}
        subtitle={t.menuSubtitle}
      />
      {loading && !stats ? (
        <div className="mt-4 rounded-3xl border border-white/10 bg-tg-surface p-4">
          <LoadingPulse label={t.loading} />
        </div>
      ) : null}
      {stats ? <StarMerchantCard stats={stats} t={t} onOpenBuyStars={onOpenBuyStars} /> : null}
      <button
        type="button"
        onClick={onOpenGift}
        className="mt-4 w-full rounded-2xl border border-fuchsia-400/35 bg-fuchsia-400/12 px-4 py-4 text-left text-tg-text"
      >
        <p className="text-sm font-semibold">{t.claimGift}</p>
        <p className="mt-1 text-xs text-tg-muted">{t.claimGiftDesc}</p>
      </button>
      <AppFooter
        supportUrl={supportUrl}
        supportLabel={t.support}
        languageLabel={t.language}
        onOpenLanguage={onOpenLanguage}
      />
    </>
  );
}
