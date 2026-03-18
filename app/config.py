
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./spyton.db'
    app_env: str = 'development'
    app_secret: str = 'change-me-strong-secret'
    admin_password: str = 'change-me-admin-password'
    telegram_bot_token: str = ''
    telegram_init_max_age: int = 3600
    ton_wallet_address: str = ''
    toncenter_api_key: str = ''
    toncenter_base_url: str = 'https://toncenter.com/api/v3'
    dexscreener_base_url: str = 'https://api.dexscreener.com'
    upload_dir: str = 'app/static/uploads'
    app_base_url: str = 'http://127.0.0.1:8000'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)


settings = Settings()
