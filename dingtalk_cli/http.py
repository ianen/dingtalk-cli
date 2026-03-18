from __future__ import annotations

import time
from typing import Any

import requests

from dingtalk_cli.config import get_required_app_credentials, load_token_cache, save_token_cache
from dingtalk_cli.errors import ApiError, ConfigError


API_BASE = "https://api.dingtalk.com"
LEGACY_API_BASE = "https://oapi.dingtalk.com"
TOKEN_BUFFER_SECONDS = 300
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class DingtalkClient:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        app_key, app_secret = get_required_app_credentials()
        token_cache = load_token_cache()
        access_token = token_cache.get("access_token", "")
        acquired_at = float(token_cache.get("acquired_at", 0))
        expires_in = int(token_cache.get("expires_in", 0))
        if (
            not force_refresh
            and access_token
            and acquired_at
            and expires_in
            and (time.time() < acquired_at + expires_in - TOKEN_BUFFER_SECONDS)
        ):
            return access_token

        response = self.session.post(
            f"{API_BASE}/v1.0/oauth2/accessToken",
            json={"appKey": app_key, "appSecret": app_secret},
            timeout=30,
        )
        payload = self._parse_response(response)
        access_token = payload.get("accessToken", "")
        expires_in = int(payload.get("expireIn", 0))
        if not access_token or not expires_in:
            raise ApiError(
                "获取 accessToken 失败，返回结果缺少 accessToken 或 expireIn。",
                code="invalid_access_token_response",
                details={"payload": payload},
            )
        save_token_cache(
            {
                "access_token": access_token,
                "expires_in": expires_in,
                "acquired_at": time.time(),
            }
        )
        return access_token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_legacy: bool = False,
        include_token: bool = True,
        timeout: int = 30,
    ) -> Any:
        base_url = LEGACY_API_BASE if use_legacy else API_BASE
        headers: dict[str, str] = {}
        refreshed = False

        for attempt in range(1, 4):
            if include_token:
                headers["x-acs-dingtalk-access-token"] = self.get_access_token(force_refresh=refreshed)
            response = self.session.request(
                method=method,
                url=f"{base_url}{path}",
                params=params,
                json=json_data,
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 401 and include_token and not refreshed:
                refreshed = True
                continue
            if response.status_code in RETRY_STATUS_CODES and attempt < 3:
                time.sleep(attempt)
                continue
            return self._parse_response(response)
        raise ApiError("请求钉钉接口失败，已达到最大重试次数。", code="retry_exhausted")

    def resolve_union_id_from_user_id(self, user_id: str) -> str:
        app_key, app_secret = get_required_app_credentials()
        token_payload = self.request(
            "GET",
            "/gettoken",
            params={"appkey": app_key, "appsecret": app_secret},
            use_legacy=True,
            include_token=False,
        )
        legacy_token = token_payload.get("access_token", "")
        if not legacy_token:
            raise ApiError(
                "获取旧版 access_token 失败。",
                code="missing_legacy_access_token",
                details={"payload": token_payload},
            )
        user_payload = self.request(
            "POST",
            "/topapi/v2/user/get",
            params={"access_token": legacy_token},
            json_data={"userid": user_id},
            use_legacy=True,
            include_token=False,
        )
        union_id = (
            user_payload.get("result", {}).get("unionid")
            or user_payload.get("result", {}).get("unionId")
            or user_payload.get("result", {}).get("union_id")
        )
        if not union_id:
            raise ApiError(
                "通过 userId 未获取到 unionId。",
                code="missing_union_id",
                details={"payload": user_payload},
            )
        return union_id

    def get(self, path: str, *, params: dict[str, Any] | None = None, use_legacy: bool = False) -> Any:
        return self.request("GET", path, params=params, use_legacy=use_legacy)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        use_legacy: bool = False,
        include_token: bool = True,
    ) -> Any:
        return self.request(
            "POST",
            path,
            params=params,
            json_data=json_data,
            use_legacy=use_legacy,
            include_token=include_token,
        )

    def put(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("PUT", path, params=params, json_data=json_data)

    def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, params=params)

    def _parse_response(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if 200 <= response.status_code < 300:
            if payload.get("errcode") not in (None, 0):
                raise ApiError(
                    payload.get("errmsg", "旧版钉钉接口返回错误。"),
                    code=str(payload.get("errcode")),
                    http_status=response.status_code,
                    details={"payload": payload},
                )
            return payload or {}

        code = None
        message = response.text or "钉钉接口调用失败。"
        details: dict[str, Any] = {}
        if isinstance(payload, dict) and payload:
            code = payload.get("code") or payload.get("errcode")
            message = (
                payload.get("message")
                or payload.get("errmsg")
                or payload.get("errorMsg")
                or message
            )
            details["payload"] = payload
        raise ApiError(message, code=str(code) if code is not None else None, http_status=response.status_code, details=details)
