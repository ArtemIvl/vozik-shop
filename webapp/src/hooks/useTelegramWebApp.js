import { useEffect, useMemo, useState } from "react";

export function useTelegramWebApp() {
  const [tgUser, setTgUser] = useState(null);
  const [initData, setInitData] = useState("");
  const [isTelegramWebApp, setIsTelegramWebApp] = useState(null);

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp) {
      setIsTelegramWebApp(false);
      return;
    }

    webApp.ready();
    webApp.expand();
    webApp.disableVerticalSwipes?.();
    webApp.setHeaderColor?.("#18222d");
    webApp.setBackgroundColor?.("#0f1116");
    setTgUser(webApp.initDataUnsafe?.user || null);
    setInitData(webApp.initData || "");
    setIsTelegramWebApp(Boolean(webApp.initData));
  }, []);

  const userLabel = useMemo(() => {
    if (!tgUser) return "Telegram user";
    const fullName = [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ").trim();
    if (fullName) return fullName;
    if (tgUser.username) return tgUser.username;
    return "Telegram user";
  }, [tgUser]);

  const initials = useMemo(() => {
    if (!tgUser) return "TG";
    const first = tgUser.first_name?.[0] || "";
    const second = tgUser.last_name?.[0] || tgUser.username?.[0] || "";
    return `${first}${second}`.toUpperCase() || "TG";
  }, [tgUser]);

  const sendData = (payload) => {
    const webApp = window.Telegram?.WebApp;
    if (!webApp) return;

    webApp.HapticFeedback?.impactOccurred("light");
    webApp.sendData(JSON.stringify(payload));
  };

  return {
    tgUser,
    userLabel,
    initials,
    initData,
    isTelegramWebApp,
    sendData
  };
}
