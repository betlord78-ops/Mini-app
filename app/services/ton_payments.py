
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.services.utils import decimal_close_enough


class PaymentLookupError(Exception):
    pass


@dataclass
class PaymentMatch:
    found: bool
    tx_hash: str | None = None
    sender_address: str | None = None
    amount_received: float | None = None
    comment: str | None = None
    confirmations: int = 0
    checked_at: datetime | None = None
    raw: dict[str, Any] | None = None
    reason: str | None = None


async def verify_ton_payment(expected_amount_ton: float, memo: str) -> PaymentMatch:
    if not settings.ton_wallet_address:
        raise PaymentLookupError('TON_WALLET_ADDRESS is not configured.')

    params = {'account': settings.ton_wallet_address, 'limit': 50, 'sort': 'desc'}
    headers = {'accept': 'application/json'}
    if settings.toncenter_api_key:
        headers['X-API-Key'] = settings.toncenter_api_key

    url = f"{settings.toncenter_base_url.rstrip('/')}/transactions"
    async with httpx.AsyncClient(timeout=25) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    txs = payload.get('transactions') or payload.get('result') or []
    for tx in txs:
        comment = _extract_comment(tx)
        amount = _extract_amount_ton(tx)
        if comment != memo or amount is None or not decimal_close_enough(expected_amount_ton, amount):
            continue
        return PaymentMatch(
            found=True,
            tx_hash=tx.get('hash') or (tx.get('transaction_id') or {}).get('hash'),
            sender_address=_extract_sender(tx),
            amount_received=amount,
            comment=comment,
            confirmations=1,
            checked_at=datetime.now(timezone.utc),
            raw=tx,
        )
    return PaymentMatch(found=False, checked_at=datetime.now(timezone.utc), reason='No matching inbound payment found yet.')


def _extract_comment(tx: dict[str, Any]) -> str | None:
    in_msg = tx.get('in_msg') or {}
    for source in [in_msg, in_msg.get('message_content') or {}, in_msg.get('decoded') or {}, in_msg.get('msg_data') or {}]:
        if isinstance(source, dict):
            for key in ('comment', 'text'):
                value = source.get(key)
                if value:
                    return value
    return None


def _extract_amount_ton(tx: dict[str, Any]) -> float | None:
    in_msg = tx.get('in_msg') or {}
    raw = in_msg.get('value') or tx.get('value')
    if raw is None:
        return None
    try:
        return int(raw) / 1_000_000_000
    except Exception:
        try:
            return float(raw)
        except Exception:
            return None


def _extract_sender(tx: dict[str, Any]) -> str | None:
    in_msg = tx.get('in_msg') or {}
    return in_msg.get('source') or in_msg.get('src')
