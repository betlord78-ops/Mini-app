# SpyTON Backend - CORS Fixed

## Railway start command

```bash
/bin/sh -c 'uvicorn run:app --host 0.0.0.0 --port $PORT'
```

## Healthcheck

`/health`

## Optional env var

`CORS_ORIGINS=https://front-alpha-three-87.vercel.app,http://localhost:3000`

Add your final frontend domain to `CORS_ORIGINS` if it changes.
