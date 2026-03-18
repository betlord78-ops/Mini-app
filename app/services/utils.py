
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


def decimal_close_enough(expected: float, actual: float, tolerance: float = 0.000001) -> bool:
    return abs(expected - actual) <= tolerance


def make_memo(prefix: str = 'SPY') -> str:
    return f"{prefix}{secrets.token_hex(4).upper()}"


def public_upload_path(filename: str) -> tuple[str, str]:
    ext = Path(filename).suffix.lower() or '.bin'
    name = f"{secrets.token_hex(12)}{ext}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    full_path = upload_dir / name
    relative = f"/static/uploads/{name}"
    return str(full_path), relative


async def save_upload(file: UploadFile) -> tuple[str, str, str]:
    full_path, relative = public_upload_path(file.filename or 'upload.bin')
    content = await file.read()
    with open(full_path, 'wb') as f:
        f.write(content)
    kind = file.content_type or 'application/octet-stream'
    return full_path, relative, kind


def package_price(service_type: str, package_name: str) -> Decimal:
    price_map = {
        'trending': {'1h': '25', '3h': '60', '6h': '100', '12h': '180', '24h': '320'},
        'ads': {'1d': '35', '3d': '90', '7d': '180'},
        'verification': {'standard': '50'},
        'listing': {'standard': '30'},
    }
    return Decimal(price_map.get(service_type, {}).get(package_name, '0'))


def activation_window(service_type: str, package_name: str) -> tuple[datetime, datetime]:
    start = datetime.utcnow()
    if service_type == 'trending':
        hours = {'1h': 1, '3h': 3, '6h': 6, '12h': 12, '24h': 24}.get(package_name, 24)
        return start, start + timedelta(hours=hours)
    if service_type == 'ads':
        days = {'1d': 1, '3d': 3, '7d': 7}.get(package_name, 1)
        return start, start + timedelta(days=days)
    return start, start


def dumps_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)
