# SpyTON Backend

FastAPI backend for the SpyTON frontend.

## Features
- Token list
- Trending tokens
- Boosted tokens
- Token detail by slug
- Vote endpoint
- Submit token endpoint
- SQLite by default
- PostgreSQL-ready with `DATABASE_URL`

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn run:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

## Railway deploy

Start command:

```bash
/bin/sh -c 'uvicorn run:app --host 0.0.0.0 --port $PORT'
```

Healthcheck path:

```text
/health
```

Recommended env vars:
- `DATABASE_URL`
- `FRONTEND_URL`

## API routes
- `GET /health`
- `GET /api/tokens`
- `GET /api/tokens/trending`
- `GET /api/tokens/boosted`
- `GET /api/tokens/{slug}`
- `POST /api/tokens/{slug}/vote`
- `POST /api/submit`
- `GET /api/submissions`
