
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Token(Base):
    __tablename__ = 'tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False)
    contract_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pool_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    x_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    supply: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    burned_lp: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    liquidity_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    volume_24h: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    holders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default='Unknown')
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    media_items: Mapped[list['MediaAsset']] = relationship('MediaAsset', back_populates='token', cascade='all, delete-orphan')
    orders: Mapped[list['Order']] = relationship('Order', back_populates='token')


class MediaAsset(Base):
    __tablename__ = 'media_assets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int | None] = mapped_column(ForeignKey('tokens.id', ondelete='SET NULL'), nullable=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    token: Mapped[Token | None] = relationship('Token', back_populates='media_items')


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_type: Mapped[str] = mapped_column(String(40), nullable=False)
    package_name: Mapped[str] = mapped_column(String(60), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_id: Mapped[int | None] = mapped_column(ForeignKey('tokens.id', ondelete='SET NULL'), nullable=True)
    token_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_symbol: Mapped[str | None] = mapped_column(String(40), nullable=True)
    contract_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    x_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_asset_id: Mapped[int | None] = mapped_column(ForeignKey('media_assets.id', ondelete='SET NULL'), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), default='TON')
    memo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    invoice_address: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default='awaiting_payment')
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    token: Mapped[Token | None] = relationship('Token', back_populates='orders')
    payment: Mapped['Payment' | None] = relationship('Payment', back_populates='order', uselist=False, cascade='all, delete-orphan')
    media_asset: Mapped[MediaAsset | None] = relationship('MediaAsset')


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'), unique=True)
    tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_received: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='unpaid')
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order: Mapped[Order] = relationship('Order', back_populates='payment')
