import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title='SpyTON Backend', version='1.1.0')

# CORS
raw_origins = os.getenv('CORS_ORIGINS', 'https://front-alpha-three-87.vercel.app,http://localhost:3000')
allow_origins = [o.strip() for o in raw_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class Token(BaseModel):
    id: int
    slug: str
    name: str
    symbol: str
    description: str
    category: str
    logo_url: str = ''
    website: str = ''
    telegram: str = ''
    twitter: str = ''
    contract_address: str
    pool_address: str
    chain: str = 'TON'
    price_usd: float
    market_cap: float
    liquidity: float
    volume_24h: float
    is_boosted: bool = False
    is_verified: bool = False
    upvotes: int = 0
    created_at: str

class Submission(BaseModel):
    name: str
    symbol: str
    description: str
    website: Optional[str] = ''
    telegram: Optional[str] = ''
    twitter: Optional[str] = ''
    contract_address: str
    category: Optional[str] = 'Launch'

TOKENS: List[Token] = [
    Token(id=1, slug='spy-shield', name='Spy Shield', symbol='SHIELD', description='Security-first TON launch with fast community momentum.', category='Security', website='https://spyton.app', telegram='https://t.me/spyton', twitter='https://x.com/spyton', contract_address='EQDShieldExampleAddress0001', pool_address='EQDShieldPool0001', price_usd=0.0081, market_cap=225000.0, liquidity=71000.0, volume_24h=91000.0, is_boosted=True, is_verified=True, upvotes=88, created_at=datetime.utcnow().isoformat()),
    Token(id=2, slug='ton-radar', name='TON Radar', symbol='RADAR', description='Fresh TON token tracking with fast growth.', category='Analytics', website='https://example.org/radar', telegram='https://t.me/spyton', twitter='https://x.com/spyton', contract_address='EQDRadarExampleAddress0002', pool_address='EQDRadarPool0002', price_usd=0.0042, market_cap=410000.0, liquidity=96000.0, volume_24h=141000.0, is_boosted=False, is_verified=True, upvotes=57, created_at=datetime.utcnow().isoformat()),
    Token(id=3, slug='blue-vault', name='Blue Vault', symbol='VAULT', description='Community-driven TON project with stable liquidity.', category='Launch', website='https://example.org/vault', telegram='https://t.me/spyton', twitter='https://x.com/spyton', contract_address='EQDVaultExampleAddress0003', pool_address='EQDVaultPool0003', price_usd=0.0114, market_cap=670000.0, liquidity=121000.0, volume_24h=203000.0, is_boosted=True, is_verified=False, upvotes=43, created_at=datetime.utcnow().isoformat()),
]
SUBMISSIONS: list[dict] = []

@app.get('/')
def root():
    return {'ok': True, 'service': 'spyton-backend', 'cors_origins': allow_origins}

@app.get('/health')
def health():
    return {'ok': True, 'service': 'spyton-backend'}

@app.get('/api/tokens', response_model=List[Token])
def get_tokens():
    return TOKENS

@app.get('/api/tokens/trending', response_model=List[Token])
def get_trending():
    return sorted(TOKENS, key=lambda t: t.upvotes, reverse=True)

@app.get('/api/tokens/boosted', response_model=List[Token])
def get_boosted():
    return [t for t in TOKENS if t.is_boosted]

@app.get('/api/tokens/{slug}', response_model=Token)
def get_token(slug: str):
    for t in TOKENS:
        if t.slug == slug:
            return t
    raise HTTPException(status_code=404, detail='Token not found')

@app.post('/api/tokens/{slug}/vote')
def vote_token(slug: str):
    for idx, t in enumerate(TOKENS):
        if t.slug == slug:
            updated = t.model_copy(update={'upvotes': t.upvotes + 1})
            TOKENS[idx] = updated
            return {'ok': True, 'slug': slug, 'upvotes': updated.upvotes}
    raise HTTPException(status_code=404, detail='Token not found')

@app.post('/api/submit')
def submit_token(payload: Submission):
    entry = payload.model_dump()
    entry['id'] = len(SUBMISSIONS) + 1
    entry['created_at'] = datetime.utcnow().isoformat()
    SUBMISSIONS.append(entry)
    return {'ok': True, 'submission': entry}

@app.get('/api/submissions')
def get_submissions():
    return SUBMISSIONS
