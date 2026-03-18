from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from .database import Base


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    symbol = Column(String(32), nullable=False)
    description = Column(Text, default='')
    category = Column(String(80), default='Launch')
    logo_url = Column(String(500), default='')
    website = Column(String(500), default='')
    telegram = Column(String(500), default='')
    twitter = Column(String(500), default='')
    contract_address = Column(String(255), unique=True, nullable=False)
    pool_address = Column(String(255), default='')
    chain = Column(String(50), default='TON')
    price_usd = Column(Float, default=0.0)
    market_cap = Column(Float, default=0.0)
    liquidity = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    upvotes = Column(Integer, default=0)
    is_boosted = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(120), nullable=False)
    ticker = Column(String(32), nullable=False)
    contract_address = Column(String(255), nullable=False)
    website = Column(String(500), default='')
    telegram = Column(String(500), default='')
    twitter = Column(String(500), default='')
    description = Column(Text, default='')
    status = Column(String(32), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
