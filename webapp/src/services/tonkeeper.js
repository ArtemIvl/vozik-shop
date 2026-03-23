export function openTonkeeper({ deepLink, webLink }) {
  const webApp = window.Telegram?.WebApp;
  webApp?.HapticFeedback?.impactOccurred("light");

  if (webApp?.openLink && webLink) {
    webApp.openLink(webLink);
    return;
  }

  if (webApp?.openTelegramLink && webLink) {
    webApp.openTelegramLink(webLink);
    return;
  }

  if (deepLink) {
    window.location.href = deepLink;
  }
}
