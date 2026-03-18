
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers.api import router as api_router
from app.routers.web import router as web_router
from app.seed import seed_db

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_db(db)

app = FastAPI(title='SpyTON Hub')
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret)
app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(web_router)
app.include_router(api_router)
