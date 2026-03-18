from datetime import datetime
from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    name: str
    symbol: str
    description: str = ''
    category: str = 'Launch'
    logo_url: str = ''
    website: str = ''
    telegram: str = ''
    twitter: str = ''
    contract_address: str
    pool_address: str = ''
    chain: str = 'TON'
    price_usd: float = 0.0
    market_cap: float = 0.0
    liquidity: float = 0.0
    volume_24h: float = 0.0
    is_boosted: bool = False
    is_verified: bool = False


class TokenCreate(TokenBase):
    upvotes: int = 0


class TokenOut(TokenBase):
    id: int
    slug: str
    upvotes: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    project_name: str = Field(..., min_length=2)
    ticker: str = Field(..., min_length=1)
    contract_address: str = Field(..., min_length=8)
    website: str = ''
    telegram: str = ''
    twitter: str = ''
    description: str = ''


class SubmissionOut(BaseModel):
    id: int
    project_name: str
    ticker: str
    contract_address: str
    website: str
    telegram: str
    twitter: str
    description: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
