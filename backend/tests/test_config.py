import os

from app.config import get_settings
from app.db import _settings


def test_test_process_disables_dotenv_before_app_imports():
    assert os.environ["KAOWOYIXIA_ENV_FILE"] == ""
    assert _settings.database_url == "sqlite://"
    assert _settings.deepseek_api_key == ""


def test_empty_settings_env_file_skips_dotenv(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DAILY_GENERATE_LIMIT=99\n", encoding="utf-8")
    monkeypatch.delenv("DAILY_GENERATE_LIMIT", raising=False)

    monkeypatch.setenv("KAOWOYIXIA_ENV_FILE", str(env_file))
    assert get_settings().daily_generate_limit == 99

    monkeypatch.setenv("KAOWOYIXIA_ENV_FILE", "")
    assert get_settings().daily_generate_limit == 3
