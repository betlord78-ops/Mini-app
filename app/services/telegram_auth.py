from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import parse_qsl

from app.config import settings


class TelegramAuthError(Exception):
    pass


def validate_init_data(init_data: str) -> dict:
    if not settings.telegram_bot_token:
        raise TelegramAuthError('TELEGRAM_BOT_TOKEN is not configured.')
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    their_hash = pairs.pop('hash', None)
    if not their_hash:
        raise TelegramAuthError('Missing Telegram hash.')

    auth_date = int(pairs.get('auth_date', '0') or '0')
    if auth_date and int(time.time()) - auth_date > settings.telegram_init_max_age:
        raise TelegramAuthError('Telegram init data expired.')

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b'WebAppData', settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, their_hash):
        raise TelegramAuthError('Invalid Telegram signature.')
    return {'ok': True, 'user': pairs.get('user'), 'auth_date': auth_date, 'query_id': pairs.get('query_id')}
