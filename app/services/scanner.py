
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class ScanResult:
    ok: bool
    query: str
    source: str
    token_name: str | None = None
    token_symbol: str | None = None
    token_address: str | None = None
    pair_address: str | None = None
    dex_id: str | None = None
    image_url: str | None = None
    website_url: str | None = None
    telegram_url: str | None = None
    twitter_url: str | None = None
    price_usd: float | None = None
    market_cap: float | None = None
    liquidity_usd: float | None = None
    volume_24h: float | None = None
    buys_24h: int | None = None
    sells_24h: int | None = None
    price_change_24h: float | None = None
    dex_url: str | None = None
    risk_level: str = 'Unknown'
    status_cards: list[tuple[str, str]] | None = None
    error: str | None = None
    raw: dict[str, Any] | None = None


async def scan_token(query: str) -> ScanResult:
    query = query.strip()
    if not query:
        return ScanResult(ok=False, query=query, source='local', error='Empty query.')

    exact = await _fetch_token_pairs(query)
    if exact:
        pair = next((p for p in exact if p.get('chainId') == 'ton'), exact[0])
        return _build_scan_result(query, pair, 'DexScreener token-pairs')

    search = await _search_pairs(query)
    if search:
        pair = next((p for p in search if p.get('chainId') == 'ton'), search[0])
        return _build_scan_result(query, pair, 'DexScreener search')

    return ScanResult(ok=False, query=query, source='DexScreener', error='No TON token or pair matched the query.')


async def _fetch_token_pairs(token_address: str) -> list[dict[str, Any]]:
    url = f"{settings.dexscreener_base_url.rstrip('/')}/token-pairs/v1/ton/{token_address}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
    return []


async def _search_pairs(query: str) -> list[dict[str, Any]]:
    url = f"{settings.dexscreener_base_url.rstrip('/')}/latest/dex/search"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params={'q': query})
        if resp.status_code == 200:
            return resp.json().get('pairs') or []
    return []


def _build_scan_result(query: str, pair: dict[str, Any], source: str) -> ScanResult:
    info = pair.get('info') or {}
    websites = info.get('websites') or []
    socials = info.get('socials') or []
    website = websites[0].get('url') if websites else None
    telegram = next((s.get('url') for s in socials if s.get('type') in {'telegram', 'tg'}), None)
    twitter = next((s.get('url') for s in socials if s.get('type') in {'twitter', 'x'}), None)
    liquidity_usd = _safe_float((pair.get('liquidity') or {}).get('usd'))
    market_cap = _safe_float(pair.get('marketCap') or pair.get('fdv'))
    txns_24h = (pair.get('txns') or {}).get('h24') or {}

    risk = 'Low'
    if liquidity_usd is None or liquidity_usd < 5000:
        risk = 'High'
    elif liquidity_usd < 25000:
        risk = 'Caution'

    status_cards = [
        ('Contract Located', '✅'),
        ('Pair Found', '✅' if pair.get('pairAddress') else '—'),
        ('Liquidity Present', '✅' if liquidity_usd else '—'),
        ('Website Found', '✅' if website else '—'),
        ('Telegram Found', '✅' if telegram else '—'),
        ('Risk Level', risk),
    ]

    return ScanResult(
        ok=True,
        query=query,
        source=source,
        token_name=(pair.get('baseToken') or {}).get('name'),
        token_symbol=(pair.get('baseToken') or {}).get('symbol'),
        token_address=(pair.get('baseToken') or {}).get('address'),
        pair_address=pair.get('pairAddress'),
        dex_id=pair.get('dexId'),
        image_url=info.get('imageUrl'),
        website_url=website,
        telegram_url=telegram,
        twitter_url=twitter,
        price_usd=_safe_float(pair.get('priceUsd')),
        market_cap=market_cap,
        liquidity_usd=liquidity_usd,
        volume_24h=_safe_float((pair.get('volume') or {}).get('h24')),
        buys_24h=txns_24h.get('buys'),
        sells_24h=txns_24h.get('sells'),
        price_change_24h=_safe_float((pair.get('priceChange') or {}).get('h24')),
        dex_url=pair.get('url'),
        risk_level=risk,
        status_cards=status_cards,
        raw=pair,
    )


def _safe_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except Exception:
        return None
