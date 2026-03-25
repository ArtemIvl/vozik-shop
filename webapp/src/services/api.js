const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin;

function buildUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export async function createMiniAppStarsOrder(payload) {
  const response = await fetch(buildUrl("/external/miniapp/stars/order"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
    } else if (typeof detail !== "string") {
      detail = rawText || `HTTP ${response.status}`;
    }
    throw new Error(`Failed to create order: ${detail}`);
  }

  return data;
}

export async function getMiniAppStarsQuote(payload) {
  const response = await fetch(buildUrl("/external/miniapp/stars/quote"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
    } else if (typeof detail !== "string") {
      detail = rawText || `HTTP ${response.status}`;
    }
    throw new Error(`Failed to load stars quote: ${detail}`);
  }

  return data;
}

export async function createMiniAppPremiumOrder(payload) {
  const response = await fetch(buildUrl("/external/miniapp/premium/order"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
    } else if (typeof detail !== "string") {
      detail = rawText || `HTTP ${response.status}`;
    }
    throw new Error(`Failed to create order: ${detail}`);
  }

  return data;
}

export async function getMiniAppPendingOrders(payload) {
  const response = await fetch(buildUrl("/external/miniapp/orders/pending"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
    } else if (typeof detail !== "string") {
      detail = rawText || `HTTP ${response.status}`;
    }
    throw new Error(`Failed to load pending orders: ${detail}`);
  }

  return data;
}

export async function getMiniAppGiftPromo(payload) {
  const response = await fetch(buildUrl("/external/miniapp/gift-promo"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => item?.msg || JSON.stringify(item)).join("; ");
    } else if (typeof detail !== "string") {
      detail = rawText || `HTTP ${response.status}`;
    }
    throw new Error(`Failed to load gift promo: ${detail}`);
  }

  return data;
}

export async function getMiniAppProfile(payload) {
  const response = await fetch(buildUrl("/external/miniapp/profile"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load profile");
  }
  return data;
}

export async function createMiniAppWithdraw(payload) {
  const response = await fetch(buildUrl("/external/miniapp/withdraw"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to create withdrawal");
  }
  return data;
}

export async function setMiniAppWallet(payload) {
  const response = await fetch(buildUrl("/external/miniapp/wallet/set"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to save wallet");
  }
  return data;
}

export async function getMiniAppLanguage(payload) {
  const response = await fetch(buildUrl("/external/miniapp/language"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load language");
  }
  return data;
}

export async function setMiniAppLanguage(payload) {
  const response = await fetch(buildUrl("/external/miniapp/language/set"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to update language");
  }
  return data;
}

export async function cancelMiniAppOrder(payload) {
  const response = await fetch(buildUrl("/external/miniapp/order/cancel"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to cancel order");
  }
  return data;
}

export async function getMiniAppOrderPaymentLink(payload) {
  const response = await fetch(buildUrl("/external/miniapp/order/payment-link"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load payment link");
  }
  return data;
}

export async function createMiniAppSellStarsOrder(payload) {
  const response = await fetch(buildUrl("/external/miniapp/sell-stars/order"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to create sell stars order");
  }
  return data;
}

export async function getMiniAppSellStarsQuote(payload) {
  const response = await fetch(buildUrl("/external/miniapp/sell-stars/quote"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load sell stars quote");
  }
  return data;
}

export async function getMiniAppPendingSellStarsOrders(payload) {
  const response = await fetch(buildUrl("/external/miniapp/sell-stars/pending"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to load pending sell stars orders");
  }
  return data;
}

export async function getMiniAppSellStarsInvoice(payload) {
  const response = await fetch(buildUrl("/external/miniapp/sell-stars/invoice"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to create invoice");
  }
  return data;
}

export async function cancelMiniAppSellStarsOrder(payload) {
  const response = await fetch(buildUrl("/external/miniapp/sell-stars/cancel"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const rawText = await response.text();
  let data = {};
  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.detail || "Failed to cancel sell stars order");
  }
  return data;
}
