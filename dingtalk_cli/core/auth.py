from __future__ import annotations

from dingtalk_cli.config import (
    get_config_path,
    get_token_path,
    load_config,
    load_token_cache,
    mask_secret,
    update_config,
)
from dingtalk_cli.errors import ValidationError
from dingtalk_cli.http import DingtalkClient


def _resolve_operator_id(
    *,
    operator_union_id: str | None,
    operator_user_id: str | None,
    client: DingtalkClient | None = None,
) -> str | None:
    if operator_union_id and operator_user_id:
        raise ValidationError("`--operator-union-id` 和 `--operator-user-id` 不能同时提供。")
    if operator_user_id:
        client = client or DingtalkClient()
        return client.resolve_union_id_from_user_id(operator_user_id)
    return operator_union_id


def setup_auth(
    *,
    app_key: str,
    app_secret: str,
    operator_union_id: str | None = None,
    operator_user_id: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    operator_id = _resolve_operator_id(
        operator_union_id=operator_union_id,
        operator_user_id=operator_user_id,
        client=client,
    )
    config = update_config(app_key=app_key, app_secret=app_secret, operator_id=operator_id)
    return {
        "configured": True,
        "ready": bool(config.get("app_key") and config.get("app_secret") and config.get("operator_id")),
        "config_path": str(get_config_path()),
        "token_path": str(get_token_path()),
        "app_key": mask_secret(config.get("app_key")),
        "app_secret": mask_secret(config.get("app_secret")),
        "operator_id": mask_secret(config.get("operator_id")),
    }


def set_operator_id(
    *,
    operator_union_id: str | None = None,
    operator_user_id: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    operator_id = _resolve_operator_id(
        operator_union_id=operator_union_id,
        operator_user_id=operator_user_id,
        client=client,
    )
    if not operator_id:
        raise ValidationError("必须提供 `--operator-union-id` 或 `--operator-user-id`。")
    config = update_config(operator_id=operator_id)
    return {
        "operator_id": mask_secret(config.get("operator_id")),
        "config_path": str(get_config_path()),
    }


def get_auth_status(*, client: DingtalkClient | None = None) -> dict:
    config = load_config()
    token_cache = load_token_cache()
    status = {
        "configured": bool(config.get("app_key") and config.get("app_secret")),
        "operator_configured": bool(config.get("operator_id")),
        "ready": bool(config.get("app_key") and config.get("app_secret") and config.get("operator_id")),
        "config_path": str(get_config_path()),
        "token_path": str(get_token_path()),
        "app_key": mask_secret(config.get("app_key")),
        "operator_id": mask_secret(config.get("operator_id")),
        "token_cached": bool(token_cache.get("access_token")),
    }
    if status["configured"]:
        client = client or DingtalkClient()
        try:
            token = client.get_access_token()
            status["token_valid"] = True
            status["access_token"] = mask_secret(token)
        except Exception as exc:
            status["token_valid"] = False
            status["token_error"] = str(exc)
    return status
