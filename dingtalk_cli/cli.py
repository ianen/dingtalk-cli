from __future__ import annotations

import functools
import sys
from pathlib import Path
from typing import Sequence

import click

from dingtalk_cli.core import auth, documents, members, nodes, workbooks, workspaces
from dingtalk_cli.errors import DingtalkCliError, ValidationError
from dingtalk_cli.output import emit_error, emit_success, set_output_state
from dingtalk_cli.repl import run_repl


PROGRAM_NAME = "dingtalk-cli"


class CliCommandError(click.ClickException):
    def __init__(self, error: DingtalkCliError) -> None:
        super().__init__(error.message)
        self.error = error
        self.exit_code = error.exit_code

    def show(self, file=None) -> None:
        emit_error(self.error, file=file)


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CliCommandError:
            raise
        except DingtalkCliError as exc:
            raise CliCommandError(exc) from exc

    return wrapper


def _require_one_of(values: dict[str, str | None], *, label: str) -> None:
    if sum(bool(value) for value in values.values()) != 1:
        options = "、".join(values.keys())
        raise ValidationError(f"{label} 必须且只能提供 {options} 其中一个。")


def _require_yes(yes: bool, *, action: str) -> None:
    if not yes:
        raise ValidationError(f"{action} 是破坏性操作，必须显式传入 `--yes`。")


def _read_content(content: str | None, content_file: str | None) -> str:
    if bool(content) == bool(content_file):
        raise ValidationError("必须且只能提供 `--content` 或 `--content-file` 其中一个。")
    if content is not None:
        return content
    try:
        return Path(content_file or "").expanduser().read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"未找到内容文件：{content_file}") from exc


@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="输出结构化 JSON。")
@click.pass_context
def cli(ctx: click.Context, use_json: bool) -> None:
    set_output_state(json_output=use_json, repl_mode=False)
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.command()
@handle_errors
def repl() -> None:
    run_repl(dispatch)


@cli.group("auth")
def auth_group() -> None:
    """认证与配置。"""


@auth_group.command("setup")
@click.option("--app-key", required=True, help="钉钉应用 appKey。")
@click.option("--app-secret", required=True, help="钉钉应用 appSecret。")
@click.option("--operator-union-id", default=None, help="操作人 unionId。")
@click.option("--operator-user-id", default=None, help="操作人 userId，CLI 会自动换取 unionId。")
@handle_errors
def auth_setup(app_key: str, app_secret: str, operator_union_id: str | None, operator_user_id: str | None) -> None:
    data = auth.setup_auth(
        app_key=app_key,
        app_secret=app_secret,
        operator_union_id=operator_union_id,
        operator_user_id=operator_user_id,
    )
    emit_success(data, "已保存认证配置。")


@auth_group.command("set-operator")
@click.option("--operator-union-id", default=None, help="操作人 unionId。")
@click.option("--operator-user-id", default=None, help="操作人 userId，CLI 会自动换取 unionId。")
@handle_errors
def auth_set_operator(operator_union_id: str | None, operator_user_id: str | None) -> None:
    data = auth.set_operator_id(operator_union_id=operator_union_id, operator_user_id=operator_user_id)
    emit_success(data, "已更新 operatorId。")


@auth_group.command("status")
@handle_errors
def auth_status() -> None:
    emit_success(auth.get_auth_status())


@cli.group()
def workspace() -> None:
    """知识库操作。"""


@workspace.command("list")
@click.option("--all", "include_all", is_flag=True, help="读取全部分页。")
@click.option("--max-results", default=20, show_default=True, type=int, help="单页数量。")
@handle_errors
def workspace_list(include_all: bool, max_results: int) -> None:
    emit_success(workspaces.list_workspaces(include_all=include_all, max_results=max_results))


@workspace.command("info")
@click.argument("workspace_id")
@handle_errors
def workspace_info(workspace_id: str) -> None:
    emit_success(workspaces.get_workspace_info(workspace_id))


@cli.group()
def node() -> None:
    """知识库节点操作。"""


@node.command("list")
@click.option("--workspace-id", default=None, help="知识库 ID。")
@click.option("--parent-node-id", default=None, help="父节点 ID。")
@click.option("--all", "include_all", is_flag=True, help="读取全部分页。")
@click.option("--max-results", default=50, show_default=True, type=int, help="单页数量。")
@handle_errors
def node_list(workspace_id: str | None, parent_node_id: str | None, include_all: bool, max_results: int) -> None:
    emit_success(
        nodes.list_nodes(
            workspace_id=workspace_id,
            parent_node_id=parent_node_id,
            include_all=include_all,
            max_results=max_results,
        )
    )


@node.command("info")
@click.argument("node_id")
@handle_errors
def node_info(node_id: str) -> None:
    emit_success(nodes.get_node_info(node_id))


@node.command("resolve-url")
@click.argument("url")
@handle_errors
def node_resolve_url(url: str) -> None:
    emit_success(nodes.resolve_node_url(url))


@cli.group()
def doc() -> None:
    """普通文档操作。"""


@doc.command("create")
@click.option("--workspace-id", required=True, help="知识库 ID。")
@click.option("--name", required=True, help="文档标题。")
@handle_errors
def doc_create(workspace_id: str, name: str) -> None:
    emit_success(
        documents.create_document(workspace_id, name),
        "已创建文档。后续立即读写请优先使用返回结果中的 `doc_key`。",
    )


@doc.command("read")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--doc-key", default=None, help="文档 docKey。")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "blocks", "both"], case_sensitive=False),
    default="text",
    show_default=True,
    help="返回格式。",
)
@handle_errors
def doc_read(node_id: str | None, url: str | None, doc_key: str | None, output_format: str) -> None:
    emit_success(documents.read_document(node_id=node_id, url=url, doc_key=doc_key, output_format=output_format))


@doc.command("overwrite")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--doc-key", default=None, help="文档 docKey。")
@click.option("--content", default=None, help="直接传入 Markdown 内容。")
@click.option("--content-file", default=None, help="读取 Markdown 文件内容。")
@click.option("--yes", is_flag=True, help="确认覆盖写入。")
@handle_errors
def doc_overwrite(
    node_id: str | None,
    url: str | None,
    doc_key: str | None,
    content: str | None,
    content_file: str | None,
    yes: bool,
) -> None:
    _require_yes(yes, action="文档覆盖写入")
    emit_success(
        documents.overwrite_document(
            node_id=node_id,
            url=url,
            doc_key=doc_key,
            content=_read_content(content, content_file),
        ),
        "已覆盖文档内容。",
    )


@doc.command("delete")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--workspace-id", default=None, help="可选。若已知 workspace_id，可与 --node-id 直接配合删除。")
@click.option("--yes", is_flag=True, help="确认删除。")
@handle_errors
def doc_delete(node_id: str | None, url: str | None, workspace_id: str | None, yes: bool) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="删除目标")
    _require_yes(yes, action="文档删除")
    emit_success(
        documents.delete_document(node_id=node_id, url=url, workspace_id=workspace_id),
        "已删除文档。",
    )


@cli.group()
def workbook() -> None:
    """`.axls` 钉钉表格操作。"""


@workbook.command("sheets")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="表格 URL。")
@handle_errors
def workbook_sheets(node_id: str | None, url: str | None) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="workbook 目标")
    emit_success(workbooks.list_sheets(node_id=node_id, url=url))


@workbook.command("info")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="表格 URL。")
@click.option("--sheet-id", required=True, help="工作表 ID。")
@handle_errors
def workbook_info(node_id: str | None, url: str | None, sheet_id: str) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="workbook 目标")
    emit_success(workbooks.get_sheet_info(node_id=node_id, url=url, sheet_id=sheet_id))


@workbook.command("read")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="表格 URL。")
@click.option("--sheet-id", default=None, help="工作表 ID，默认读取第一个。")
@click.option("--range", "range_address", default="A1:Z80", show_default=True, help="读取区域。")
@handle_errors
def workbook_read(node_id: str | None, url: str | None, sheet_id: str | None, range_address: str) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="workbook 目标")
    emit_success(workbooks.read_sheet_range(node_id=node_id, url=url, sheet_id=sheet_id, range_address=range_address))


@cli.group()
def member() -> None:
    """文档成员管理。"""


@member.command("add")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--member-id", required=True, help="成员 userId。")
@click.option("--role", "role_type", type=click.Choice(["viewer", "editor"]), required=True, help="权限类型。")
@handle_errors
def member_add(node_id: str | None, url: str | None, member_id: str, role_type: str) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="成员目标")
    emit_success(members.add_member(node_id=node_id, url=url, member_id=member_id, role_type=role_type), "已添加成员。")


@member.command("update")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--member-id", required=True, help="成员 userId。")
@click.option("--role", "role_type", type=click.Choice(["viewer", "editor"]), required=True, help="权限类型。")
@handle_errors
def member_update(node_id: str | None, url: str | None, member_id: str, role_type: str) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="成员目标")
    emit_success(
        members.update_member(node_id=node_id, url=url, member_id=member_id, role_type=role_type),
        "已更新成员权限。",
    )


@member.command("remove")
@click.option("--node-id", default=None, help="节点 ID。")
@click.option("--url", default=None, help="文档 URL。")
@click.option("--member-id", required=True, help="成员 userId。")
@click.option("--yes", is_flag=True, help="确认移除。")
@handle_errors
def member_remove(node_id: str | None, url: str | None, member_id: str, yes: bool) -> None:
    _require_one_of({"--node-id": node_id, "--url": url}, label="成员目标")
    _require_yes(yes, action="成员移除")
    emit_success(members.remove_member(node_id=node_id, url=url, member_id=member_id), "已移除成员。")


def dispatch(args: Sequence[str] | None = None, exit_on_error: bool = True) -> int:
    argv = list(args or [])
    use_json = "--json" in argv
    set_output_state(json_output=use_json, repl_mode=not exit_on_error)
    try:
        cli.main(args=argv, prog_name=PROGRAM_NAME, standalone_mode=False)
        return 0
    except CliCommandError as exc:
        emit_error(exc.error)
        if exit_on_error:
            raise SystemExit(exc.exit_code) from exc
        return exc.exit_code
    except click.ClickException as exc:
        if use_json:
            emit_error(
                DingtalkCliError(
                    exc.format_message(),
                    error_type=type(exc).__name__,
                    code="click_error",
                )
            )
        else:
            exc.show()
        if exit_on_error:
            raise SystemExit(exc.exit_code) from exc
        return exc.exit_code
    except DingtalkCliError as exc:
        emit_error(exc)
        if exit_on_error:
            raise SystemExit(exc.exit_code) from exc
        return exc.exit_code
    except Exception as exc:
        emit_error(DingtalkCliError(str(exc), error_type=type(exc).__name__, code="unexpected_error"))
        if exit_on_error:
            raise SystemExit(1) from exc
        return 1


def main() -> None:
    dispatch(sys.argv[1:], True)
