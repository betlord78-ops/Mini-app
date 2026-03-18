
# SpyTON Hub — finished starter

This is a real, runnable SpyTON Hub starter for Telegram Mini App style usage.

Included:
- FastAPI + Jinja web app
- Home, Trending, Scan, Promote, Profile, Admin
- Token pages
- Local media uploads for banners/images/gifs/videos
- Order creation for trending, ads, verification, listing
- Memo-based TON invoice verification flow
- Telegram Mini App initData validation endpoint
- DexScreener-powered live scan/search for TON pairs
- SQLite by default, PostgreSQL-ready via DATABASE_URL
- Docker + Render/Railway-ready layout

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn run:app --reload
```

Open: http://127.0.0.1:8000

## Required production env vars

- `DATABASE_URL`
- `APP_SECRET`
- `ADMIN_PASSWORD`
- `TON_WALLET_ADDRESS`
- `TELEGRAM_BOT_TOKEN`
- `APP_BASE_URL`
- optional: `TONCENTER_API_KEY`

## Deploy

### Railway
- Push to GitHub
- Create a Railway project from repo
- Add PostgreSQL
- Set env vars from `.env.example`
- Start command:

```bash
uvicorn run:app --host 0.0.0.0 --port $PORT
```

### Render
- Push to GitHub
- Create Web Service
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn run:app --host 0.0.0.0 --port $PORT`
- Add PostgreSQL and set `DATABASE_URL`

## What is fully implemented here
- all app pages
- admin login/logout
- token creation/edit/delete in admin
- order creation + status updates
- local file upload support
- payment verify endpoint that stores result and activates order when found
- scanner page and API
- Telegram initData validation endpoint

## What still depends on your real external credentials/services
- actual inbound TON transactions reaching your wallet
- Telegram Mini App requests from your real bot
- external TON and DexScreener uptime/data quality
- your own publishing automation after approved/active orders

## Admin login
Go to `/admin/login`
Use password from `ADMIN_PASSWORD`
