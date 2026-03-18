from __future__ import annotations

from typing import Any

from dingtalk_cli.config import get_required_operator_id
from dingtalk_cli.errors import ValidationError
from dingtalk_cli.http import DingtalkClient
from dingtalk_cli.core import nodes


def extract_text_from_blocks(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in sorted(blocks, key=lambda item: item.get("index", 0)):
        block_type = block.get("blockType")
        if block_type == "heading":
            heading = block.get("heading", {})
            level = heading.get("level", "heading-1").split("-")[-1]
            prefix = "#" * int(level) if level.isdigit() else "##"
            lines.append(f"{prefix} {heading.get('text', '')}".rstrip())
        elif block_type == "paragraph":
            lines.append(block.get("paragraph", {}).get("text", ""))
        elif block_type == "unorderedList":
            lines.append(f"- {block.get('unorderedList', {}).get('text', '')}".rstrip())
        elif block_type == "orderedList":
            lines.append(f"1. {block.get('orderedList', {}).get('text', '')}".rstrip())
        elif block_type == "blockquote":
            lines.append(f"> {block.get('blockquote', {}).get('text', '')}".rstrip())
        elif block_type == "table":
            table = block.get("table", {})
            lines.append(f"[表格 {table.get('rowSize', '?')}x{table.get('colSize', '?')}]")
        else:
            unknown_text = block.get("unknown", {}).get("text", "")
            if unknown_text:
                lines.append(unknown_text)
    return "\n\n".join(line for line in lines if line).strip()


def _resolve_document_target(
    *,
    node_id: str | None = None,
    url: str | None = None,
    doc_key: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    if sum(bool(value) for value in (node_id, url, doc_key)) != 1:
        raise ValidationError("必须且只能提供 `--node-id`、`--url` 或 `--doc-key` 其中一个。")
    if doc_key:
        return {"doc_key": doc_key, "node": None}
    node = nodes.resolve_target_node(node_id=node_id, url=url, client=client)
    if node.get("extension") == "axls":
        raise ValidationError(
            "目标节点是钉钉表格 `.axls`，不能按普通文档读取。",
            suggestion="请改用 `dingtalk-cli workbook ...` 命令。",
        )
    if node.get("type") == "FOLDER":
        raise ValidationError("目标节点是文件夹，不能按文档读取。")
    return {"doc_key": node["node_id"], "node": node}


def create_document(workspace_id: str, name: str, *, client: DingtalkClient | None = None) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    payload = client.post(
        f"/v1.0/doc/workspaces/{workspace_id}/docs",
        json_data={"operatorId": operator_id, "docType": "DOC", "name": name},
    )
    return {
        "workspace_id": payload.get("workspaceId", workspace_id),
        "node_id": payload.get("nodeId"),
        "doc_key": payload.get("docKey"),
        "url": payload.get("url"),
        "name": name,
    }


def read_document(
    *,
    node_id: str | None = None,
    url: str | None = None,
    doc_key: str | None = None,
    output_format: str = "text",
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    resolved = _resolve_document_target(node_id=node_id, url=url, doc_key=doc_key, client=client)
    payload = client.get(
        f"/v1.0/doc/suites/documents/{resolved['doc_key']}/blocks",
        params={"operatorId": operator_id},
    )
    blocks = payload.get("result", {}).get("data", [])
    text = extract_text_from_blocks(blocks)
    data = {
        "doc_key": resolved["doc_key"],
        "node": resolved["node"],
        "text": text,
        "blocks": blocks,
    }
    if output_format == "text":
        return {"doc_key": data["doc_key"], "text": text}
    if output_format == "blocks":
        return {"doc_key": data["doc_key"], "blocks": blocks}
    return data


def overwrite_document(
    *,
    content: str,
    node_id: str | None = None,
    url: str | None = None,
    doc_key: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    resolved = _resolve_document_target(node_id=node_id, url=url, doc_key=doc_key, client=client)
    client.post(
        f"/v1.0/doc/suites/documents/{resolved['doc_key']}/overwriteContent",
        json_data={
            "operatorId": operator_id,
            "content": content,
            "docContent": content,
            "contentType": "markdown",
        },
    )
    return {"status": "overwritten", "doc_key": resolved["doc_key"]}


def delete_document(
    *,
    node_id: str | None = None,
    url: str | None = None,
    workspace_id: str | None = None,
    client: DingtalkClient | None = None,
) -> dict[str, Any]:
    client = client or DingtalkClient()
    operator_id = get_required_operator_id()
    if workspace_id and node_id:
        node = {"workspace_id": workspace_id, "node_id": node_id}
    else:
        node = nodes.resolve_target_node(node_id=node_id, url=url, client=client)
    client.delete(
        f"/v1.0/doc/workspaces/{node['workspace_id']}/docs/{node['node_id']}",
        params={"operatorId": operator_id},
    )
    return {
        "status": "deleted",
        "workspace_id": node["workspace_id"],
        "node_id": node["node_id"],
    }
