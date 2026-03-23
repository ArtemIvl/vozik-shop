# vozik_shop
Telegram bot which allows users to purchase Telegram Stars and Telegram Premium subscriptions at lower prices and without KYC using cryptocurrency.

## Bot setup
1. Install Python dependencies:
```bash
poetry install
```
2. Configure env:
```bash
cp .env.example .env
```
3. Start bot polling:
```bash
poetry run python src/buy_stars/main.py
```
4. Start webhook/api server (optional, for webhook routes):
```bash
poetry run python src/buy_stars/webhook_server.py
```

## Mini App setup (React + Tailwind)
Frontend is in `webapp/`.

1. Install frontend dependencies:
```bash
cd webapp
npm install
```
2. Configure frontend env:
```bash
cp .env.example .env
```
Set:
`VITE_API_BASE_URL=https://YOUR_PUBLIC_BACKEND_URL`

3. Run dev server:
```bash
npm run dev
```
4. Build production bundle:
```bash
npm run build
```

## Connect Mini App to Telegram bot
1. Host `webapp` build on an HTTPS URL (Telegram requires HTTPS for Mini Apps).
2. Start backend API/webhook server and expose it via HTTPS:
```bash
poetry run python src/buy_stars/webhook_server.py
```
3. Set `MINI_APP_URL` in `.env` to frontend public URL.
4. Set `VITE_API_BASE_URL` to backend public URL.
5. Restart bot and frontend.
6. Open bot menu. You will see `Open Mini App` button.
