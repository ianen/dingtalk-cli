from __future__ import annotations

from typing import Any

from dingtalk_cli.config import get_required_operator_id
from dingtalk_cli.http import DingtalkClient


def _normalize_workspace(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "workspace_id": item.get("workspaceId"),
        "name": item.get("name"),
        "description": item.get("description", ""),
        "root_node_id": item.get("rootNodeId"),
        "type": item.get("type"),
        "url": item.get("url"),
        "create_time": item.get("createTime"),
        "modified_time": item.get("modifiedTime"),
    }


def list_workspaces(*, include_all: bool = False, max_results: int = 20, client: DingtalkClient | None = None) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    items: list[dict[str, Any]] = []
    next_token: str | None = None
    while True:
        params = {"operatorId": operator_id, "maxResults": max_results}
        if next_token:
            params["nextToken"] = next_token
        payload = client.get("/v2.0/wiki/workspaces", params=params)
        items.extend(_normalize_workspace(item) for item in payload.get("workspaces", []))
        next_token = payload.get("nextToken")
        if not include_all or not next_token:
            break
    return {"items": items, "next_token": next_token, "has_more": bool(next_token)}


def get_workspace_info(workspace_id: str, *, client: DingtalkClient | None = None) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    payload = client.get(f"/v2.0/wiki/workspaces/{workspace_id}", params={"operatorId": operator_id})
    return _normalize_workspace(payload.get("workspace", payload))
