import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db, SessionLocal
from .models import Submission, Token
from .schemas import SubmissionCreate, SubmissionOut, TokenCreate, TokenOut
from .seed import seed_tokens
from .utils import slugify

app = FastAPI(title='SpyTON API', version='1.0.0')

frontend_url = os.getenv('FRONTEND_URL', '*')
origins = ['*'] if frontend_url == '*' else [frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_tokens(db)


@app.get('/health')
def health():
    return {'ok': True, 'service': 'spyton-backend'}


@app.get('/')
def root():
    return {'name': 'SpyTON API', 'status': 'running'}


@app.get('/api/tokens', response_model=list[TokenOut])
def list_tokens(db: Session = Depends(get_db)):
    return db.query(Token).order_by(Token.is_boosted.desc(), Token.upvotes.desc(), Token.created_at.desc()).all()


@app.get('/api/tokens/trending', response_model=list[TokenOut])
def trending_tokens(db: Session = Depends(get_db)):
    return db.query(Token).order_by(Token.upvotes.desc(), Token.volume_24h.desc()).limit(20).all()


@app.get('/api/tokens/boosted', response_model=list[TokenOut])
def boosted_tokens(db: Session = Depends(get_db)):
    return db.query(Token).filter(Token.is_boosted.is_(True)).order_by(Token.created_at.desc()).all()


@app.get('/api/tokens/{slug}', response_model=TokenOut)
def get_token(slug: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.slug == slug).first()
    if not token:
        raise HTTPException(status_code=404, detail='Token not found')
    return token


@app.post('/api/tokens', response_model=TokenOut)
def create_token(payload: TokenCreate, db: Session = Depends(get_db)):
    existing = db.query(Token).filter(Token.contract_address == payload.contract_address).first()
    if existing:
        raise HTTPException(status_code=400, detail='Token already exists')

    base_slug = slugify(payload.name)
    slug = base_slug
    counter = 2
    while db.query(Token).filter(Token.slug == slug).first():
        slug = f'{base_slug}-{counter}'
        counter += 1

    token = Token(slug=slug, **payload.model_dump())
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


@app.post('/api/tokens/{slug}/vote', response_model=TokenOut)
def upvote_token(slug: str, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.slug == slug).first()
    if not token:
        raise HTTPException(status_code=404, detail='Token not found')
    token.upvotes += 1
    db.commit()
    db.refresh(token)
    return token


@app.post('/api/submit', response_model=SubmissionOut)
def submit_token(payload: SubmissionCreate, db: Session = Depends(get_db)):
    submission = Submission(**payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@app.get('/api/submissions', response_model=list[SubmissionOut])
def list_submissions(db: Session = Depends(get_db)):
    return db.query(Submission).order_by(Submission.created_at.desc()).all()
