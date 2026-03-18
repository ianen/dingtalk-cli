from __future__ import annotations

from typing import Any

from dingtalk_cli.config import get_required_operator_id
from dingtalk_cli.errors import ValidationError
from dingtalk_cli.http import DingtalkClient
from dingtalk_cli.core import nodes


def _resolve_workbook_target(
    *,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    node = nodes.resolve_target_node(node_id=node_id, url=url, client=client)
    if node.get("extension") != "axls":
        raise ValidationError(
            "目标节点不是 `.axls` 钉钉表格。",
            suggestion="普通文档请使用 `doc` 命令，AI 表格请使用对应 notable 能力。",
        )
    return node


def list_sheets(
    *,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    node = _resolve_workbook_target(node_id=node_id, url=url, client=client)
    payload = client.get(
        f"/v1.0/doc/workbooks/{node['node_id']}/sheets",
        params={"operatorId": operator_id},
    )
    items = [
        {"sheet_id": item.get("id"), "name": item.get("name")}
        for item in payload.get("value", [])
    ]
    return {"workbook_id": node["node_id"], "items": items}


def get_sheet_info(
    *,
    sheet_id: str,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    node = _resolve_workbook_target(node_id=node_id, url=url, client=client)
    payload = client.get(
        f"/v1.0/doc/workbooks/{node['node_id']}/sheets/{sheet_id}",
        params={"operatorId": operator_id},
    )
    return {"workbook_id": node["node_id"], "sheet": payload}


def read_sheet_range(
    *,
    range_address: str = "A1:Z80",
    sheet_id: str | None = None,
    node_id: str | None = None,
    url: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    workbook = list_sheets(node_id=node_id, url=url, client=client)
    if not workbook["items"]:
        raise ValidationError("该 `.axls` 表格中没有可读取的工作表。")
    sheet = next((item for item in workbook["items"] if item["sheet_id"] == sheet_id), None)
    if sheet_id and sheet is None:
        raise ValidationError(f"未找到 sheet `{sheet_id}`。")
    if sheet is None:
        sheet = workbook["items"][0]
    operator_id = get_required_operator_id()
    payload = client.get(
        f"/v1.0/doc/workbooks/{workbook['workbook_id']}/sheets/{sheet['sheet_id']}/ranges/{range_address}",
        params={"operatorId": operator_id, "select": "displayValues"},
    )
    return {
        "workbook_id": workbook["workbook_id"],
        "sheet": sheet,
        "range": range_address,
        "display_values": payload.get("displayValues", []),
    }
