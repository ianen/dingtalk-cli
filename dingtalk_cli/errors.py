from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def suggest_from_error(
    http_status: int | None,
    code: str | None,
    message: str,
) -> str | None:
    if code == "MissingoperatorId":
        return "请先配置 operator unionId。可通过 `auth setup` 或 `auth set-operator` 完成。"
    if code == "paramError":
        return "operatorId 必须是 unionId，不是 userId。若只有 userId，可使用 `--operator-user-id` 自动换取。"
    if code == "Forbidden.AccessDenied.AccessTokenPermissionDenied":
        return "应用权限不足。请根据 requiredScopes 在钉钉开放平台开通对应 scope。"
    if code == "InvalidAction.NotFound":
        return "接口路径不存在。请检查 API 版本号、资源 ID 和目标类型。"
    if http_status == 429:
        return "命中钉钉限流，请稍后重试。"
    if "Target document should be doc." in message:
        return "目标节点不是普通文档，若是 `.axls` 请改用 `workbook` 命令。"
    if "The given baseId is incorrect" in message:
        return "当前文件不是 AI 表格 base；若节点扩展名是 `.axls`，请改用 `workbook` 命令。"
    return None


@dataclass
class DingtalkCliError(Exception):
    message: str
    error_type: str = "DingtalkCliError"
    code: str | None = None
    http_status: int | None = None
    suggestion: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 1

    def __post_init__(self) -> None:
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "type": self.error_type,
            "code": self.code,
            "http_status": self.http_status,
            "message": self.message,
            "suggestion": self.suggestion,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ConfigError(DingtalkCliError):
    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(
            message=message,
            error_type="ConfigError",
            code="config_error",
            suggestion=suggestion,
        )


class ValidationError(DingtalkCliError):
    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(
            message=message,
            error_type="ValidationError",
            code="validation_error",
            suggestion=suggestion,
        )


class ApiError(DingtalkCliError):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        http_status: int | None = None,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_type="ApiError",
            code=code,
            http_status=http_status,
            suggestion=suggestion or suggest_from_error(http_status, code, message),
            details=details or {},
        )
