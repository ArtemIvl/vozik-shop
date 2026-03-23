import { useEffect, useState } from "react";
import AppShell from "./components/layout/AppShell";
import BottomNav from "./components/layout/BottomNav";
import MainMenuPage from "./pages/MainMenuPage";
import BuyStarsPage from "./pages/BuyStarsPage";
import BuyPremiumPage from "./pages/BuyPremiumPage";
import SellStarsPage from "./pages/SellStarsPage";
import GiftPromoPage from "./pages/GiftPromoPage";
import ProfilePage from "./pages/ProfilePage";
import LanguageModal from "./components/common/LanguageModal";
import LoadingPulse from "./components/common/LoadingPulse";
import { useTelegramWebApp } from "./hooks/useTelegramWebApp";
import { getMiniAppPendingOrders, getMiniAppPendingSellStarsOrders } from "./services/api";
import { useAppLanguage } from "./hooks/useAppLanguage";

export default function App() {
  const { tgUser, userLabel, initials, initData, isTelegramWebApp, sendData } = useTelegramWebApp();
  const { language, t, loadLanguage, updateLanguage, languageLoading } = useAppLanguage(initData);
  const [activePage, setActivePage] = useState("menu");
  const [languageOpen, setLanguageOpen] = useState(false);
  const [visitedPages, setVisitedPages] = useState(() => new Set(["menu"]));
  const [pendingCounts, setPendingCounts] = useState({
    buy_stars: 0,
    buy_tg_premium: 0,
    sell_stars: 0
  });

  const refreshPendingCounts = async () => {
    if (!initData) return;
    try {
      const [stars, premium, sellStars] = await Promise.all([
        getMiniAppPendingOrders({ init_data: initData, order_type: "stars" }),
        getMiniAppPendingOrders({ init_data: initData, order_type: "premium" }),
        getMiniAppPendingSellStarsOrders({ init_data: initData })
      ]);

      setPendingCounts({
        buy_stars: stars?.orders?.length || 0,
        buy_tg_premium: premium?.orders?.length || 0,
        sell_stars: sellStars?.orders?.length || 0
      });
    } catch {
      setPendingCounts({
        buy_stars: 0,
        buy_tg_premium: 0,
        sell_stars: 0
      });
    }
  };

  useEffect(() => {
    refreshPendingCounts();
  }, [initData]);

  useEffect(() => {
    loadLanguage();
  }, [initData]);

  const handleNavSelect = (id) => {
    setVisitedPages((current) => {
      const next = new Set(current);
      next.add(id);
      return next;
    });
    if (id === "buy_stars") {
      setActivePage("buy_stars");
      return;
    }
    if (id === "buy_premium") {
      setActivePage("buy_premium");
      return;
    }
    if (id === "gift_promo") {
      setActivePage("gift_promo");
      return;
    }
    if (id === "sell_stars") {
      setActivePage("sell_stars");
      return;
    }
    if (id === "profile") {
      setActivePage("profile");
      return;
    }
    setActivePage("menu");
    sendData({ event: "menu_action", action: id });
  };

  if (isTelegramWebApp === false) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-md items-center justify-center px-4 text-tg-text">
        <div className="rounded-[2rem] border border-white/10 bg-tg-surface p-6 text-center shadow-panel">
          <p className="text-sm uppercase tracking-[0.18em] text-[#FFD767]">Telegram only</p>
          <h1 className="mt-3 text-2xl font-semibold text-tg-text">This app is not available here</h1>
          <p className="mt-3 text-sm leading-6 text-tg-muted">
            Open this page from the Telegram bot mini app to continue.
          </p>
        </div>
      </main>
    );
  }

  return (
    <AppShell
      scrollKey={activePage}
      bottomNav={(
        <BottomNav
          activePage={activePage}
          onSelect={handleNavSelect}
          pendingCounts={pendingCounts}
          t={t}
        />
      )}
    >
      <LanguageModal
        open={languageOpen}
        current={language}
        onClose={() => setLanguageOpen(false)}
        onSelect={async (code) => {
          await updateLanguage(code);
          setLanguageOpen(false);
        }}
        closeLabel={t.close}
        title={t.chooseLanguage}
      />

      {languageLoading ? (
        <div className="mb-4 rounded-2xl border border-white/10 bg-tg-surface p-4">
          <LoadingPulse label={t.loading} />
        </div>
      ) : null}

      {visitedPages.has("menu") ? (
        <div className={activePage === "menu" ? "block" : "hidden"}>
          <MainMenuPage
            userLabel={userLabel}
            initials={initials}
            initData={initData}
            t={t}
            supportUrl="https://t.me/VozikShop_support"
            onOpenLanguage={() => setLanguageOpen(true)}
            onOpenGift={() => {
              setVisitedPages((current) => new Set(current).add("gift_promo"));
              setActivePage("gift_promo");
            }}
          />
        </div>
      ) : null}

      {visitedPages.has("buy_stars") ? (
        <div className={activePage === "buy_stars" ? "block" : "hidden"}>
          <BuyStarsPage
            initData={initData}
            tgUser={tgUser}
            sendData={sendData}
            isActive={activePage === "buy_stars"}
            onOrdersUpdated={refreshPendingCounts}
            t={t}
          />
        </div>
      ) : null}

      {visitedPages.has("buy_premium") ? (
        <div className={activePage === "buy_premium" ? "block" : "hidden"}>
          <BuyPremiumPage
            initData={initData}
            tgUser={tgUser}
            sendData={sendData}
            isActive={activePage === "buy_premium"}
            onOrdersUpdated={refreshPendingCounts}
            t={t}
          />
        </div>
      ) : null}

      {visitedPages.has("gift_promo") ? (
        <div className={activePage === "gift_promo" ? "block" : "hidden"}>
          <GiftPromoPage
            initData={initData}
            t={t}
          />
        </div>
      ) : null}

      {visitedPages.has("sell_stars") ? (
        <div className={activePage === "sell_stars" ? "block" : "hidden"}>
          <SellStarsPage
            initData={initData}
            isActive={activePage === "sell_stars"}
            onOrdersUpdated={refreshPendingCounts}
            t={t}
          />
        </div>
      ) : null}

      {visitedPages.has("profile") ? (
        <div className={activePage === "profile" ? "block" : "hidden"}>
          <ProfilePage
            initData={initData}
            t={t}
          />
        </div>
      ) : null}
    </AppShell>
  );
}
