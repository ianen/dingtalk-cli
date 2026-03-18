from __future__ import annotations

from dingtalk_cli.config import get_required_operator_id
from dingtalk_cli.http import DingtalkClient
from dingtalk_cli.core import nodes


def _resolve_member_target(
    *,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    return nodes.resolve_target_node(node_id=node_id, url=url, client=client)


def add_member(
    *,
    member_id: str,
    role_type: str,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    node = _resolve_member_target(node_id=node_id, url=url, client=client)
    client.post(
        f"/v1.0/doc/workspaces/{node['workspace_id']}/docs/{node['node_id']}/members",
        json_data={
            "operatorId": operator_id,
            "members": [{"id": member_id, "roleType": role_type}],
        },
    )
    return {
        "status": "added",
        "workspace_id": node["workspace_id"],
        "node_id": node["node_id"],
        "member_id": member_id,
        "role_type": role_type,
    }


def update_member(
    *,
    member_id: str,
    role_type: str,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    node = _resolve_member_target(node_id=node_id, url=url, client=client)
    client.put(
        f"/v1.0/doc/workspaces/{node['workspace_id']}/docs/{node['node_id']}/members/{member_id}",
        json_data={"operatorId": operator_id, "roleType": role_type},
    )
    return {
        "status": "updated",
        "workspace_id": node["workspace_id"],
        "node_id": node["node_id"],
        "member_id": member_id,
        "role_type": role_type,
    }


def remove_member(
    *,
    member_id: str,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    node = _resolve_member_target(node_id=node_id, url=url, client=client)
    client.delete(
        f"/v1.0/doc/workspaces/{node['workspace_id']}/docs/{node['node_id']}/members/{member_id}",
        params={"operatorId": operator_id},
    )
    return {
        "status": "removed",
        "workspace_id": node["workspace_id"],
        "node_id": node["node_id"],
        "member_id": member_id,
    }
