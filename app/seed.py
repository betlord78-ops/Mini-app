
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Token


SEED_TOKENS = [
    {
        'name': 'SpyTON', 'symbol': 'SPY', 'contract_address': 'EQSpyTonExample111', 'pool_address': 'EQPoolSpy111',
        'website_link': 'https://example.com', 'telegram_link': 'https://t.me/example', 'x_link': 'https://x.com/example',
        'description': 'SpyTON flagship token card.', 'supply': '100,000,000', 'decimals': 9, 'burned_lp': '95,000,000 (95%)',
        'price_usd': Decimal('0.0042'), 'market_cap': Decimal('420000'), 'liquidity_usd': Decimal('54000'), 'volume_24h': Decimal('91000'),
        'holders': 1240, 'age_label': '2h', 'risk_level': 'Low', 'is_verified': True, 'is_promoted': True, 'is_trending': True,
    },
    {
        'name': 'TonRadar', 'symbol': 'RADAR', 'contract_address': 'EQRadarExample222', 'pool_address': 'EQPoolRadar222',
        'description': 'Fresh TON launch example.', 'supply': '50,000,000', 'decimals': 9, 'burned_lp': '21,000,000 (42%)',
        'price_usd': Decimal('0.0019'), 'market_cap': Decimal('95000'), 'liquidity_usd': Decimal('18000'), 'volume_24h': Decimal('22000'),
        'holders': 327, 'age_label': '5h', 'risk_level': 'Caution', 'is_verified': False, 'is_promoted': False, 'is_trending': True,
    },
]


def seed_db(db: Session):
    exists = db.scalar(select(Token.id).limit(1))
    if exists:
        return
    for item in SEED_TOKENS:
        db.add(Token(**item))
    db.commit()
