from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from dingtalk_cli.errors import ConfigError


CONFIG_DIR_ENV = "DINGTALK_CLI_CONFIG_DIR"
APP_KEY_ENV = "DINGTALK_APP_KEY"
APP_SECRET_ENV = "DINGTALK_APP_SECRET"
OPERATOR_ID_ENV = "DINGTALK_OPERATOR_ID"

DEFAULT_CONFIG_DIR_NAME = ".dingtalk-cli"
CONFIG_FILE_NAME = "config.json"
TOKEN_FILE_NAME = "token.json"


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return f"{value[0]}***"
    return f"{value[:4]}****"


def get_config_dir() -> Path:
    override = os.getenv(CONFIG_DIR_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / DEFAULT_CONFIG_DIR_NAME


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILE_NAME


def get_token_path() -> Path:
    return get_config_dir() / TOKEN_FILE_NAME


def _ensure_config_dir() -> Path:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_config_dir()
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def load_config() -> dict[str, Any]:
    config = _load_json(get_config_path())
    if os.getenv(APP_KEY_ENV):
        config["app_key"] = os.getenv(APP_KEY_ENV, "").strip()
    if os.getenv(APP_SECRET_ENV):
        config["app_secret"] = os.getenv(APP_SECRET_ENV, "").strip()
    if os.getenv(OPERATOR_ID_ENV):
        config["operator_id"] = os.getenv(OPERATOR_ID_ENV, "").strip()
    return config


def save_config(config: dict[str, Any]) -> None:
    _write_json(get_config_path(), config)


def update_config(**updates: Any) -> dict[str, Any]:
    config = _load_json(get_config_path())
    for key, value in updates.items():
        if value is not None:
            config[key] = value
    save_config(config)
    return load_config()


def load_token_cache() -> dict[str, Any]:
    return _load_json(get_token_path())


def save_token_cache(token_cache: dict[str, Any]) -> None:
    _write_json(get_token_path(), token_cache)


def clear_token_cache() -> None:
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()


def get_required_operator_id() -> str:
    operator_id = load_config().get("operator_id", "").strip()
    if not operator_id:
        raise ConfigError(
            "未配置 operator unionId。",
            suggestion="请先运行 `dingtalk-cli auth setup --operator-union-id <UNION_ID>` 或 `auth set-operator`。",
        )
    return operator_id


def get_required_app_credentials() -> tuple[str, str]:
    config = load_config()
    app_key = config.get("app_key", "").strip()
    app_secret = config.get("app_secret", "").strip()
    if not app_key or not app_secret:
        raise ConfigError(
            "未配置 appKey/appSecret。",
            suggestion="请先运行 `dingtalk-cli auth setup --app-key <APP_KEY> --app-secret <APP_SECRET>`。",
        )
    return app_key, app_secret
