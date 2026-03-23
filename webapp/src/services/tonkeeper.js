export function openExternalLink(url) {
  if (!url) return;

  const webApp = window.Telegram?.WebApp;
  webApp?.HapticFeedback?.impactOccurred("light");

  if (webApp?.openLink) {
    webApp.openLink(url);
    return;
  }

  if (webApp?.openTelegramLink) {
    webApp.openTelegramLink(url);
    return;
  }

  window.open(url, "_blank", "noopener,noreferrer");
}

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
