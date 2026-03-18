from __future__ import annotations

import os

import pytest

from dingtalk_cli.core import auth, documents, nodes, workbooks, workspaces


REQUIRED_ENV = [
    "DINGTALK_CLI_E2E",
    "DINGTALK_APP_KEY",
    "DINGTALK_APP_SECRET",
    "DINGTALK_OPERATOR_ID",
    "DINGTALK_TEST_WORKSPACE_ID",
]


def _missing_required_env() -> list[str]:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if os.environ.get("DINGTALK_CLI_E2E") == "1":
        return [name for name in missing if name != "DINGTALK_CLI_E2E"]
    return missing


missing_env = _missing_required_env()
if missing_env:
    pytestmark = pytest.mark.skip(reason=f"E2E disabled or missing env: {', '.join(missing_env)}")


def test_auth_status_live() -> None:
    data = auth.get_auth_status()
    assert data["configured"] is True
    assert data["operator_configured"] is True


def test_workspace_live() -> None:
    data = workspaces.list_workspaces(include_all=False)
    assert isinstance(data["items"], list)
    info = workspaces.get_workspace_info(os.environ["DINGTALK_TEST_WORKSPACE_ID"])
    assert info["workspace_id"] == os.environ["DINGTALK_TEST_WORKSPACE_ID"]


def test_document_lifecycle_live() -> None:
    workspace_id = os.environ["DINGTALK_TEST_WORKSPACE_ID"]
    created = documents.create_document(workspace_id, "dingtalk-cli e2e temp")
    try:
        read = documents.read_document(doc_key=created["doc_key"], output_format="both")
        assert read["doc_key"] == created["doc_key"]
        overwritten = documents.overwrite_document(doc_key=created["doc_key"], content="# e2e\n\ncontent")
        assert overwritten["status"] == "overwritten"
    finally:
        deleted = documents.delete_document(node_id=created["node_id"], workspace_id=created["workspace_id"])
        assert deleted["status"] == "deleted"


@pytest.mark.skipif(not os.environ.get("DINGTALK_TEST_WORKBOOK_NODE_ID"), reason="Missing DINGTALK_TEST_WORKBOOK_NODE_ID")
def test_workbook_live() -> None:
    node_id = os.environ["DINGTALK_TEST_WORKBOOK_NODE_ID"]
    node = nodes.get_node_info(node_id)
    assert node["extension"] == "axls"
    sheets = workbooks.list_sheets(node_id=node_id)
    assert isinstance(sheets["items"], list)
