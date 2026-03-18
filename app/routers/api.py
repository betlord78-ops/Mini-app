
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, Payment, Token
from app.services.scanner import scan_token
from app.services.telegram_auth import TelegramAuthError, validate_init_data
from app.services.ton_payments import PaymentLookupError, verify_ton_payment
from app.services.utils import activation_window, dumps_json

router = APIRouter(prefix='/api', tags=['api'])


class TelegramInitRequest(BaseModel):
    init_data: str


@router.get('/health')
def health():
    return {'ok': True}


@router.get('/tokens')
def get_tokens(db: Session = Depends(get_db)):
    tokens = db.query(Token).all()
    return [
        {
            'id': t.id,
            'name': t.name,
            'symbol': t.symbol,
            'contract_address': t.contract_address,
            'pool_address': t.pool_address,
            'verified': t.is_verified,
            'promoted': t.is_promoted,
            'trending': t.is_trending,
            'risk_level': t.risk_level,
            'price_usd': float(t.price_usd) if t.price_usd is not None else None,
            'market_cap': float(t.market_cap) if t.market_cap is not None else None,
            'liquidity_usd': float(t.liquidity_usd) if t.liquidity_usd is not None else None,
        }
        for t in tokens
    ]


@router.get('/scan')
async def api_scan(query: str):
    result = await scan_token(query)
    return result.__dict__


@router.get('/orders/{order_id}')
def api_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return serialize_order(order)


@router.post('/orders/{order_id}/verify-payment')
async def api_verify_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    try:
        match = await verify_ton_payment(float(order.amount), order.memo)
    except PaymentLookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payment = order.payment or Payment(order_id=order.id)
    if match.found:
        payment.tx_hash = match.tx_hash
        payment.sender_address = match.sender_address
        payment.amount_received = Decimal(str(match.amount_received or 0))
        payment.comment = match.comment
        payment.status = 'paid'
        payment.raw_json = dumps_json(match.raw or {})
        order.status = 'active' if order.service_type in {'trending', 'ads'} else 'paid'
        order.paid_at = datetime.utcnow()
        if order.service_type in {'trending', 'ads'}:
            order.starts_at, order.ends_at = activation_window(order.service_type, order.package_name)
            if order.token:
                if order.service_type == 'trending':
                    order.token.is_trending = True
                if order.service_type == 'ads':
                    order.token.is_promoted = True
        db.add(payment)
        db.commit()
    else:
        payment.status = 'unpaid'
        payment.raw_json = dumps_json({'reason': match.reason, 'checked_at': match.checked_at})
        db.add(payment)
        db.commit()
    db.refresh(order)
    return {'match': match.__dict__, 'order': serialize_order(order)}


@router.post('/auth/telegram/init')
def telegram_init(payload: TelegramInitRequest):
    try:
        return validate_init_data(payload.init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def serialize_order(order: Order):
    return {
        'id': order.id,
        'service_type': order.service_type,
        'package_name': order.package_name,
        'amount': float(order.amount),
        'asset': order.asset,
        'memo': order.memo,
        'status': order.status,
        'invoice_address': order.invoice_address,
        'token_name': order.token_name,
        'token_symbol': order.token_symbol,
        'contract_address': order.contract_address,
        'payment': {
            'status': order.payment.status if order.payment else 'unpaid',
            'tx_hash': order.payment.tx_hash if order.payment else None,
            'sender_address': order.payment.sender_address if order.payment else None,
        },
    }
