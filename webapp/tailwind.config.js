/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "tg-bg": "var(--tg-bg)",
        "tg-surface": "var(--tg-surface)",
        "tg-surface-soft": "var(--tg-surface-soft)",
        "tg-card": "var(--tg-card)",
        "tg-text": "var(--tg-text)",
        "tg-muted": "var(--tg-muted)",
        star: "var(--star)",
        vozik: "var(--vozik)",
        "ink-dark": "var(--ink-dark)"
      },
      boxShadow: {
        panel: "0 14px 30px rgba(0, 0, 0, 0.32)"
      }
    }
  },
  plugins: []
};
