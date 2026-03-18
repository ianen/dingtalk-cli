from __future__ import annotations

from typing import Any

from dingtalk_cli.config import get_required_operator_id
from dingtalk_cli.errors import ValidationError
from dingtalk_cli.http import DingtalkClient
from dingtalk_cli.core import workspaces


def _normalize_node(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": item.get("nodeId"),
        "name": item.get("name"),
        "type": item.get("type"),
        "category": item.get("category"),
        "extension": item.get("extension", ""),
        "workspace_id": item.get("workspaceId"),
        "url": item.get("url"),
        "create_time": item.get("createTime"),
        "modified_time": item.get("modifiedTime"),
    }


def list_nodes(
    *,
    parent_node_id: str | None = None,
    workspace_id: str | None = None,
    include_all: bool = False,
    max_results: int = 50,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    if bool(parent_node_id) == bool(workspace_id):
        raise ValidationError("必须且只能提供 `--parent-node-id` 或 `--workspace-id` 其中一个。")
    client = client or DingtalkClient()
    if workspace_id:
        parent_node_id = workspaces.get_workspace_info(workspace_id, client=client)["root_node_id"]
    operator_id = get_required_operator_id()
    items: list[dict[str, Any]] = []
    next_token: str | None = None
    while True:
        params = {
            "parentNodeId": parent_node_id,
            "operatorId": operator_id,
            "maxResults": max_results,
        }
        if next_token:
            params["nextToken"] = next_token
        payload = client.get("/v2.0/wiki/nodes", params=params)
        items.extend(_normalize_node(item) for item in payload.get("nodes", []))
        next_token = payload.get("nextToken")
        if not include_all or not next_token:
            break
    return {
        "items": items,
        "parent_node_id": parent_node_id,
        "next_token": next_token,
        "has_more": bool(next_token),
    }


def get_node_info(node_id: str, *, client: DingtalkClient | None = None) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    payload = client.get(f"/v2.0/wiki/nodes/{node_id}", params={"operatorId": operator_id})
    return _normalize_node(payload.get("node", payload))


def resolve_node_url(url: str, *, client: DingtalkClient | None = None) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    payload = client.post(
        "/v2.0/wiki/nodes/queryByUrl",
        params={"operatorId": operator_id},
        json_data={"url": url, "operatorId": operator_id},
    )
    return _normalize_node(payload.get("node", payload))


def resolve_target_node(
    *,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    if bool(node_id) == bool(url):
        raise ValidationError("必须且只能提供 `--node-id` 或 `--url` 其中一个。")
    if node_id:
        return get_node_info(node_id, client=client)
    return resolve_node_url(url or "", client=client)
