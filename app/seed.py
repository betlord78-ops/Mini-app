from sqlalchemy.orm import Session
from .models import Token
from .utils import slugify


def seed_tokens(db: Session):
    if db.query(Token).count() > 0:
        return

    sample = [
        {
            'name': 'Spy Shield',
            'symbol': 'SHIELD',
            'description': 'Security-first TON launch with fast community momentum.',
            'category': 'Security',
            'contract_address': 'EQDShieldExampleAddress0001',
            'pool_address': 'EQDShieldPool0001',
            'website': 'https://spyton.app',
            'telegram': 'https://t.me/spyton',
            'twitter': 'https://x.com/spyton',
            'price_usd': 0.0081,
            'market_cap': 225000,
            'liquidity': 71000,
            'volume_24h': 91000,
            'upvotes': 88,
            'is_boosted': True,
            'is_verified': True,
        },
        {
            'name': 'TON Radar',
            'symbol': 'RADAR',
            'description': 'Fresh TON token tracking with fast growth.',
            'category': 'Analytics',
            'contract_address': 'EQDRadarExampleAddress0002',
            'pool_address': 'EQDRadarPool0002',
            'website': 'https://example.org/radar',
            'telegram': 'https://t.me/spyton',
            'twitter': 'https://x.com/spyton',
            'price_usd': 0.0042,
            'market_cap': 410000,
            'liquidity': 96000,
            'volume_24h': 141000,
            'upvotes': 57,
            'is_boosted': False,
            'is_verified': True,
        },
        {
            'name': 'Blue Vault',
            'symbol': 'VAULT',
            'description': 'Community-driven TON project with stable liquidity.',
            'category': 'Launch',
            'contract_address': 'EQDVaultExampleAddress0003',
            'pool_address': 'EQDVaultPool0003',
            'website': 'https://example.org/vault',
            'telegram': 'https://t.me/spyton',
            'twitter': 'https://x.com/spyton',
            'price_usd': 0.0114,
            'market_cap': 670000,
            'liquidity': 121000,
            'volume_24h': 203000,
            'upvotes': 43,
            'is_boosted': True,
            'is_verified': False,
        },
    ]

    for item in sample:
        db.add(Token(slug=slugify(item['name']), **item))
    db.commit()
