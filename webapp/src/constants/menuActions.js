export function getMenuActions(t) {
  return [
    {
      id: "buy_stars",
      title: t.buyStars,
      description: t.buyStarsDesc,
      icon: "⭐",
      accent: "star"
    },
    {
      id: "buy_tg_premium",
      title: t.buyPremium,
      description: t.buyPremiumDesc,
      icon: "💎",
      accent: "premium"
    },
    {
      id: "gift_promo",
      title: t.claimGift,
      description: t.claimGiftDesc,
      icon: "🎁",
      accent: "gift"
    },
    {
      id: "sell_stars",
      title: t.sellStars,
      description: t.sellStarsDesc,
      icon: "💸",
      accent: "sell"
    },
    {
      id: "profile",
      title: t.profile,
      description: t.profileDesc,
      icon: "👤",
      accent: "profile"
    }
  ];
}
