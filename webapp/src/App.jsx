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
  const { tgUser, userLabel, initials, initData, sendData } = useTelegramWebApp();
  const { language, t, loadLanguage, updateLanguage, languageLoading } = useAppLanguage(initData);
  const [activePage, setActivePage] = useState("menu");
  const [languageOpen, setLanguageOpen] = useState(false);
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
  }, [initData, activePage]);

  useEffect(() => {
    loadLanguage();
  }, [initData]);

  const handleNavSelect = (id) => {
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

  return (
    <AppShell
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

      {activePage === "menu" ? (
        <MainMenuPage
          userLabel={userLabel}
          initials={initials}
          initData={initData}
          t={t}
          supportUrl="https://t.me/VozikShop_support"
          onOpenLanguage={() => setLanguageOpen(true)}
          onOpenGift={() => setActivePage("gift_promo")}
        />
      ) : null}

      {activePage === "buy_stars" ? (
        <BuyStarsPage
          initData={initData}
          tgUser={tgUser}
          sendData={sendData}
          onOrdersUpdated={refreshPendingCounts}
          t={t}
        />
      ) : null}

      {activePage === "buy_premium" ? (
        <BuyPremiumPage
          initData={initData}
          tgUser={tgUser}
          sendData={sendData}
          onOrdersUpdated={refreshPendingCounts}
          t={t}
        />
      ) : null}

      {activePage === "gift_promo" ? (
        <GiftPromoPage
          initData={initData}
          t={t}
        />
      ) : null}

      {activePage === "sell_stars" ? (
        <SellStarsPage
          initData={initData}
          onOrdersUpdated={refreshPendingCounts}
          t={t}
        />
      ) : null}

      {activePage === "profile" ? (
        <ProfilePage
          initData={initData}
          t={t}
        />
      ) : null}
    </AppShell>
  );
}
