
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import MediaAsset, Order, Payment, Token
from app.services.scanner import scan_token
from app.services.ton_payments import PaymentLookupError, verify_ton_payment
from app.services.utils import activation_window, dumps_json, make_memo, package_price, save_upload

router = APIRouter(tags=['web'])
templates = Jinja2Templates(directory='app/templates')


def admin_logged_in(request: Request) -> bool:
    return request.session.get('is_admin') is True


def require_admin(request: Request):
    if not admin_logged_in(request):
        raise HTTPException(status_code=403, detail='Admin login required.')


@router.get('/', response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    new_launches = db.query(Token).order_by(desc(Token.created_at)).limit(8).all()
    trending = db.query(Token).filter(Token.is_trending == True).order_by(desc(Token.market_cap)).limit(8).all()
    promoted = db.query(Token).filter(Token.is_promoted == True).order_by(desc(Token.updated_at)).limit(8).all()
    return templates.TemplateResponse('home.html', {'request': request, 'new_launches': new_launches, 'trending': trending, 'promoted': promoted})


@router.get('/trending', response_class=HTMLResponse)
def trending_page(request: Request, db: Session = Depends(get_db)):
    tokens = db.query(Token).filter(or_(Token.is_trending == True, Token.is_promoted == True)).order_by(desc(Token.market_cap), desc(Token.liquidity_usd)).all()
    return templates.TemplateResponse('trending.html', {'request': request, 'tokens': tokens})


@router.get('/scan', response_class=HTMLResponse)
async def scan_page(request: Request, query: str | None = None):
    result = await scan_token(query) if query else None
    return templates.TemplateResponse('scan.html', {'request': request, 'result': result, 'query': query or ''})


@router.get('/token/{token_id}', response_class=HTMLResponse)
def token_page(token_id: int, request: Request, db: Session = Depends(get_db)):
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail='Token not found')
    return templates.TemplateResponse('token.html', {'request': request, 'token': token})


@router.get('/promote', response_class=HTMLResponse)
def promote_page(request: Request):
    return templates.TemplateResponse('promote.html', {'request': request, 'wallet': settings.ton_wallet_address})


@router.post('/promote/create')
async def create_order(
    request: Request,
    service_type: str = Form(...),
    package_name: str = Form(...),
    customer_name: str = Form(''),
    customer_username: str = Form(''),
    token_name: str = Form(...),
    token_symbol: str = Form(''),
    contract_address: str = Form(...),
    telegram_link: str = Form(''),
    website_link: str = Form(''),
    x_link: str = Form(''),
    notes: str = Form(''),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    amount = package_price(service_type, package_name)
    if amount <= 0:
        raise HTTPException(status_code=400, detail='Unknown package selected.')

    token = db.query(Token).filter(Token.contract_address == contract_address).first()
    if not token:
        token = Token(
            name=token_name,
            symbol=token_symbol or token_name[:8].upper(),
            contract_address=contract_address,
            telegram_link=telegram_link or None,
            website_link=website_link or None,
            x_link=x_link or None,
            description=notes or None,
        )
        db.add(token)
        db.flush()

    media_asset = None
    if media and media.filename:
        _, relative, content_type = await save_upload(media)
        media_asset = MediaAsset(token_id=token.id, file_path=relative, file_type=content_type, title=media.filename)
        db.add(media_asset)
        db.flush()

    memo = make_memo('SPY')
    order = Order(
        service_type=service_type,
        package_name=package_name,
        customer_name=customer_name or None,
        customer_username=customer_username or None,
        token_id=token.id,
        token_name=token_name,
        token_symbol=token_symbol or None,
        contract_address=contract_address,
        telegram_link=telegram_link or None,
        website_link=website_link or None,
        x_link=x_link or None,
        notes=notes or None,
        media_asset_id=media_asset.id if media_asset else None,
        amount=amount,
        asset='TON',
        memo=memo,
        invoice_address=settings.ton_wallet_address or 'SET_TON_WALLET_ADDRESS',
        status='awaiting_payment',
    )
    db.add(order)
    db.flush()

    payment = Payment(order_id=order.id, status='unpaid')
    db.add(payment)
    db.commit()
    return RedirectResponse(url=f'/invoice/{order.id}', status_code=303)


@router.get('/invoice/{order_id}', response_class=HTMLResponse)
def invoice_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return templates.TemplateResponse('invoice.html', {'request': request, 'order': order, 'wallet': settings.ton_wallet_address})


@router.post('/invoice/{order_id}/verify')
async def verify_invoice(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    try:
        match = await verify_ton_payment(float(order.amount), order.memo)
    except PaymentLookupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

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
    return RedirectResponse(url=f'/invoice/{order.id}', status_code=303)


@router.get('/profile', response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(20).all()
    return templates.TemplateResponse('profile.html', {'request': request, 'orders': orders})


@router.get('/admin/login', response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse('admin_login.html', {'request': request, 'error': None})


@router.post('/admin/login', response_class=HTMLResponse)
def admin_login(request: Request, password: str = Form(...)):
    if password != settings.admin_password:
        return templates.TemplateResponse('admin_login.html', {'request': request, 'error': 'Wrong password'})
    request.session['is_admin'] = True
    return RedirectResponse(url='/admin', status_code=303)


@router.get('/admin/logout')
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/', status_code=303)


@router.get('/admin', response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    tokens = db.query(Token).order_by(desc(Token.updated_at)).all()
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(50).all()
    return templates.TemplateResponse('admin.html', {'request': request, 'tokens': tokens, 'orders': orders})


@router.post('/admin/tokens/create')
async def admin_create_token(
    request: Request,
    name: str = Form(...),
    symbol: str = Form(...),
    contract_address: str = Form(...),
    pool_address: str = Form(''),
    website_link: str = Form(''),
    telegram_link: str = Form(''),
    x_link: str = Form(''),
    supply: str = Form(''),
    decimals: int = Form(9),
    burned_lp: str = Form(''),
    risk_level: str = Form('Unknown'),
    is_verified: bool = Form(False),
    is_promoted: bool = Form(False),
    is_trending: bool = Form(False),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    require_admin(request)
    logo_url = None
    if logo and logo.filename:
        _, relative, content_type = await save_upload(logo)
        logo_url = relative
    token = Token(
        name=name, symbol=symbol, contract_address=contract_address, pool_address=pool_address or None,
        website_link=website_link or None, telegram_link=telegram_link or None, x_link=x_link or None,
        supply=supply or None, decimals=decimals, burned_lp=burned_lp or None, risk_level=risk_level,
        is_verified=is_verified, is_promoted=is_promoted, is_trending=is_trending, logo_url=logo_url,
    )
    db.add(token)
    db.commit()
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/admin/tokens/{token_id}/toggle')
def admin_toggle_token(request: Request, token_id: int, field: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request)
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail='Token not found')
    if field not in {'is_verified', 'is_promoted', 'is_trending'}:
        raise HTTPException(status_code=400, detail='Invalid field')
    setattr(token, field, not getattr(token, field))
    db.commit()
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/admin/tokens/{token_id}/delete')
def admin_delete_token(request: Request, token_id: int, db: Session = Depends(get_db)):
    require_admin(request)
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        raise HTTPException(status_code=404, detail='Token not found')
    db.delete(token)
    db.commit()
    return RedirectResponse(url='/admin', status_code=303)


@router.post('/admin/orders/{order_id}/status')
def admin_update_order_status(request: Request, order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    order.status = status
    db.commit()
    return RedirectResponse(url='/admin', status_code=303)
