from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dingtalk_cli import config
from dingtalk_cli.cli import cli
from dingtalk_cli.core import documents, members, workbooks
from dingtalk_cli.http import DingtalkClient


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DINGTALK_CLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("DINGTALK_APP_KEY", raising=False)
    monkeypatch.delenv("DINGTALK_APP_SECRET", raising=False)
    monkeypatch.delenv("DINGTALK_OPERATOR_ID", raising=False)
    return tmp_path


def _resolve_cli(name: str) -> list[str]:
    force_installed = os.environ.get("DINGTALK_CLI_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        return [path]
    if force_installed:
        raise RuntimeError(f"{name} not found in PATH. Run `pip install -e .` first.")
    return [sys.executable, "-m", "dingtalk_cli"]


class TestConfigHelpers:
    def test_config_round_trip(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})
        assert config.load_config()["app_key"] == "ak"
        assert config.get_config_path() == temp_config_dir / "config.json"
        config.save_token_cache({"access_token": "token", "expires_in": 7200, "acquired_at": 1})
        assert config.load_token_cache()["access_token"] == "token"

    def test_env_overrides_config(self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config.save_config({"app_key": "file-ak", "app_secret": "file-sk", "operator_id": "file-ou"})
        monkeypatch.setenv("DINGTALK_APP_KEY", "env-ak")
        monkeypatch.setenv("DINGTALK_APP_SECRET", "env-sk")
        monkeypatch.setenv("DINGTALK_OPERATOR_ID", "env-ou")
        loaded = config.load_config()
        assert loaded["app_key"] == "env-ak"
        assert loaded["app_secret"] == "env-sk"
        assert loaded["operator_id"] == "env-ou"


class TestAuthCommands:
    def test_auth_setup_saves_config(self, runner: CliRunner, temp_config_dir: Path) -> None:
        result = runner.invoke(
            cli,
            [
                "auth",
                "setup",
                "--app-key",
                "test-app-key",
                "--app-secret",
                "test-secret",
                "--operator-union-id",
                "union-123",
            ],
        )
        assert result.exit_code == 0
        saved = json.loads((temp_config_dir / "config.json").read_text(encoding="utf-8"))
        assert saved["app_key"] == "test-app-key"
        assert saved["operator_id"] == "union-123"

    def test_auth_setup_with_user_id_resolves_union_id(self, runner: CliRunner, temp_config_dir: Path) -> None:
        with patch("dingtalk_cli.core.auth.DingtalkClient.resolve_union_id_from_user_id", return_value="union-xyz"):
            result = runner.invoke(
                cli,
                [
                    "auth",
                    "setup",
                    "--app-key",
                    "test-app-key",
                    "--app-secret",
                    "test-secret",
                    "--operator-user-id",
                    "user-123",
                ],
            )
        assert result.exit_code == 0
        saved = json.loads((temp_config_dir / "config.json").read_text(encoding="utf-8"))
        assert saved["operator_id"] == "union-xyz"

    def test_auth_setup_rejects_both_operator_flags(self, runner: CliRunner, temp_config_dir: Path) -> None:
        result = runner.invoke(
            cli,
            [
                "--json",
                "auth",
                "setup",
                "--app-key",
                "test-app-key",
                "--app-secret",
                "test-secret",
                "--operator-union-id",
                "union-123",
                "--operator-user-id",
                "user-123",
            ],
        )
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["ok"] is False
        assert payload["error"]["type"] == "ValidationError"

    def test_auth_status_without_config(self, runner: CliRunner, temp_config_dir: Path) -> None:
        result = runner.invoke(cli, ["--json", "auth", "status"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["configured"] is False


class TestDocumentLogic:
    def test_extract_text_from_blocks(self) -> None:
        blocks = [
            {"index": 1, "blockType": "paragraph", "paragraph": {"text": "正文"}},
            {"index": 0, "blockType": "heading", "heading": {"level": "heading-2", "text": "标题"}},
            {"index": 2, "blockType": "unorderedList", "unorderedList": {"text": "列表项"}},
        ]
        text = documents.extract_text_from_blocks(blocks)
        assert "## 标题" in text
        assert "正文" in text
        assert "- 列表项" in text

    def test_doc_read_axls_returns_structured_error(self, runner: CliRunner, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})
        with patch(
            "dingtalk_cli.core.nodes.get_node_info",
            return_value={
                "node_id": "node-1",
                "workspace_id": "ws-1",
                "type": "FILE",
                "extension": "axls",
                "name": "sheet.axls",
                "url": "https://alidocs.dingtalk.com/i/nodes/node-1",
            },
        ):
            result = runner.invoke(cli, ["--json", "doc", "read", "--node-id", "node-1"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["error"]["suggestion"]
        assert "workbook" in payload["error"]["suggestion"]

    def test_doc_delete_requires_yes(self, runner: CliRunner, temp_config_dir: Path) -> None:
        result = runner.invoke(cli, ["--json", "doc", "delete", "--node-id", "node-1"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["error"]["type"] == "ValidationError"

    def test_delete_document_can_use_workspace_and_node_directly(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})

        class FakeClient:
            def __init__(self) -> None:
                self.last = None

            def delete(self, path: str, *, params=None):
                self.last = {"path": path, "params": params}
                return {}

        fake_client = FakeClient()
        data = documents.delete_document(node_id="node-1", workspace_id="ws-1", client=fake_client)
        assert data["status"] == "deleted"
        assert data["workspace_id"] == "ws-1"
        assert fake_client.last["path"].endswith("/ws-1/docs/node-1")

    def test_doc_overwrite_reads_file(self, runner: CliRunner, temp_config_dir: Path, tmp_path: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})
        content_path = tmp_path / "content.md"
        content_path.write_text("# 标题\n\n正文", encoding="utf-8")
        with patch("dingtalk_cli.core.documents.overwrite_document", return_value={"status": "overwritten", "doc_key": "doc-1"}) as mock_call:
            result = runner.invoke(
                cli,
                [
                    "--json",
                    "doc",
                    "overwrite",
                    "--doc-key",
                    "doc-1",
                    "--content-file",
                    str(content_path),
                    "--yes",
                ],
            )
        assert result.exit_code == 0
        _, kwargs = mock_call.call_args
        assert kwargs["content"] == "# 标题\n\n正文"

    def test_overwrite_document_sends_content_and_doc_content(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})

        class FakeClient:
            def __init__(self) -> None:
                self.last = None

            def post(self, path: str, *, params=None, json_data=None, use_legacy=False, include_token=True):
                self.last = {"path": path, "json_data": json_data}
                return {}

        fake_client = FakeClient()
        documents.overwrite_document(doc_key="doc-1", content="# e2e", client=fake_client)
        assert fake_client.last["path"].endswith("/doc-1/overwriteContent")
        assert fake_client.last["json_data"]["content"] == "# e2e"
        assert fake_client.last["json_data"]["docContent"] == "# e2e"


class TestWorkbookAndMembers:
    def test_workbook_read_uses_first_sheet_when_sheet_id_missing(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})

        class FakeClient:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict]] = []

            def get(self, path: str, *, params=None, use_legacy=False):
                self.calls.append((path, params or {}))
                if path.endswith("/sheets"):
                    return {"value": [{"id": "sheet-1", "name": "Sheet1"}]}
                return {"displayValues": [["标题", "值"]]}

        fake_client = FakeClient()
        with patch(
            "dingtalk_cli.core.nodes.resolve_target_node",
            return_value={"node_id": "wb-1", "extension": "axls", "workspace_id": "ws-1", "type": "FILE"},
        ):
            data = workbooks.read_sheet_range(node_id="wb-1", client=fake_client)
        assert data["sheet"]["sheet_id"] == "sheet-1"
        assert data["display_values"] == [["标题", "值"]]

    def test_member_add_payload(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})

        class FakeClient:
            def __init__(self) -> None:
                self.last = None

            def post(self, path: str, *, params=None, json_data=None, use_legacy=False, include_token=True):
                self.last = {"path": path, "json_data": json_data}
                return {}

        fake_client = FakeClient()
        with patch(
            "dingtalk_cli.core.nodes.resolve_target_node",
            return_value={"node_id": "node-1", "workspace_id": "ws-1", "type": "FILE", "extension": "doc"},
        ):
            data = members.add_member(node_id="node-1", member_id="user-1", role_type="editor", client=fake_client)
        assert data["status"] == "added"
        assert fake_client.last["path"].endswith("/ws-1/docs/node-1/members")
        assert fake_client.last["json_data"]["members"][0]["roleType"] == "editor"


class TestHttpClient:
    def test_access_token_uses_cache(self, temp_config_dir: Path) -> None:
        config.save_config({"app_key": "ak", "app_secret": "sk", "operator_id": "ou"})
        config.save_token_cache({"access_token": "cached", "expires_in": 7200, "acquired_at": 9999999999})
        client = DingtalkClient()
        assert client.get_access_token() == "cached"


class TestCliSubprocess:
    CLI_BASE = _resolve_cli("dingtalk-cli")

    def test_help(self, temp_config_dir: Path) -> None:
        result = subprocess.run(self.CLI_BASE + ["--help"], capture_output=True, text=True, check=False)
        assert result.returncode == 0
        assert "dingtalk-cli" in result.stdout

    def test_json_auth_status(self, temp_config_dir: Path) -> None:
        result = subprocess.run(self.CLI_BASE + ["--json", "auth", "status"], capture_output=True, text=True, check=False)
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert payload["data"]["configured"] is False
