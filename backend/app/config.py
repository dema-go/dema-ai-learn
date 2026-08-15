import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "sqlite:///./local.db"
    deepseek_api_key: str = ""
    default_openid: str = "dev-local-user"
    daily_generate_limit: int = 3
    material_ttl_days: int = 7
    timezone: str = "Asia/Shanghai"


def get_settings() -> Settings:
    configured_env_file = os.environ.get("KAOWOYIXIA_ENV_FILE")
    if configured_env_file is None:
        env_file = _BACKEND_DIR / ".env"
    else:
        env_file = configured_env_file or None
    return Settings(_env_file=env_file)
